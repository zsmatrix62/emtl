import json
import os
import re
from random import SystemRandom
from typing import Optional

from ddddocr import DdddOcr
from requests import Response
from requests import Session
from requests import get

from .const import _base_headers
from .const import _urls
from .error import EmAPIError
from .error import LoginFailedError
from .error import SessionExpiredError
from .utils import emt_trade_encrypt
from .utils import get_float
from .utils import get_logger

logger = get_logger(__name__)

# Global OCR instance shared by all clients
_global_ocr = DdddOcr(show_ad=False)


class EMTClient:
    """EMT client adapter for multi-user support.

    Each instance maintains its own session and validation key.
    OCR is shared globally across all clients.
    """

    def __init__(self) -> None:
        self.session = Session()
        self._em_validate_key = ""
        self.username: str = ""

    def _query_snapshot(self, symbol_code: str, market: str) -> Optional[dict]:
        url = "https://emhsmarketwg.eastmoneysec.com/api/SHSZQuoteSnapshot"
        params = {"id": symbol_code.strip(), "market": market}
        resp = self.session.get(url, params=params, headers=_base_headers.copy())
        self._check_resp(resp)
        return resp.json()

    def get_last_price(self, symbol_code: str, market: str) -> float:
        ret = self._query_snapshot(symbol_code, market)
        if ret is None or "status" not in ret or ret["status"] != 0:
            return float("nan")
        return get_float(ret["realtimequote"], "currentPrice")

    @staticmethod
    def _check_resp(resp: Response) -> None:
        """Check HTTP response for errors.

        Args:
            resp: Response object to check

        Raises:
            EmAPIError: If response indicates an error
        """
        content_type = resp.headers.get("Content-Type", "")
        is_image = "image" in content_type

        try:
            json_resp = resp.json()
        except:
            json_resp = None

        is_json = False
        if json_resp:
            try:
                json.dumps(json_resp)
                is_json = True
            except:
                ...

        if is_image:
            return

        if resp.status_code != 200:
            logger.error(f"request {resp.url} fail, code={resp.status_code}, response={resp.text}")
            raise EmAPIError(f"HTTP error: {resp.status_code}", status_code=resp.status_code, response=resp.text)

        if is_json:
            status = (json_resp or {}).get("Status")
            if status == -2:
                logger.warning(f"session expired: {resp.text}")
                raise SessionExpiredError("Session expired, please login again")
            elif status == -1:
                logger.error(f"request {resp.url} fail, code={resp.status_code}, response={resp.text}")
                raise EmAPIError(f"API error: {resp.text}", status_code=resp.status_code, response=resp.text)

    def _query_something(self, tag: str, req_data: Optional[dict] = None) -> Optional[Response]:
        """Generic query function for EMT API.

        Args:
            tag: Request type identifier
            req_data: Optional request payload data

        Returns:
            Response object or None if request fails

        Raises:
            AssertionError: If tag is not in _urls
        """
        if not self._em_validate_key:
            validate_key = self.login()
        else:
            validate_key = self._em_validate_key

        assert tag in _urls, f"{tag} not in url list"
        url = _urls[tag] + validate_key

        if req_data is None:
            req_data = {
                "qqhs": 100,
                "dwc": "",
            }

        headers = _base_headers.copy()
        headers["X-Requested-With"] = "XMLHttpRequest"
        logger.debug(f"(tag={tag}), (data={req_data}), (url={url})")

        resp = self.session.post(url, headers=headers, data=req_data)
        self._check_resp(resp)
        return resp

    def _query_something_with_retry(self, tag: str, req_data: Optional[dict] = None) -> Optional[Response]:
        """Generic query function with automatic retry on session expiration.

        Args:
            tag: Request type identifier
            req_data: Optional request payload data

        Returns:
            Response object or None if request fails

        Raises:
            AssertionError: If tag is not in _urls
            LoginFailedError: If re-login fails
        """
        try:
            return self._query_something(tag, req_data)
        except SessionExpiredError:
            # Session expired, clear cache and re-login
            self._re_login()
            # Retry the request once
            return self._query_something(tag, req_data)

    def _get_captcha_code(self) -> tuple[float, str]:
        """Get random number and captcha code.

        Returns:
            Tuple of (random_number, captcha_code)
        """
        cryptogen = SystemRandom()
        random_num = cryptogen.random()
        resp = get(f"{_urls['yzm']}{random_num}", headers=_base_headers, timeout=60)
        self._check_resp(resp)
        code = _global_ocr.classification(resp.content)
        return random_num, code

    def _get_em_validate_key(self) -> Optional[str]:
        """Get em_validatekey from the trade page.

        Returns:
            The validation key string or None if not found
        """
        url = "https://jywg.18.cn/Trade/Buy"
        resp = self.session.get(url, headers=_base_headers)
        self._check_resp(resp)
        match_result = re.findall(r'id="em_validatekey" type="hidden" value="(.*?)"', resp.text)
        if match_result:
            _em_validatekey = match_result[0].strip()
            if _em_validatekey:
                self._em_validate_key = _em_validatekey
                return _em_validatekey
        return None

    def login(self, username: str = "", password: str = "", duration: int = 180) -> Optional[str]:
        """Login to EMT trading platform.

        Args:
            username: EMT username (defaults to EM_USERNAME env var)
            password: EMT password in plaintext (defaults to EM_PASSWORD env var)
            duration: Session duration in minutes, defaults to 180

        Returns:
            Validation key string if login succeeds, None otherwise
        """
        if not username:
            username = os.getenv("EM_USERNAME", "")
        if not password:
            password = os.getenv("EM_PASSWORD", "")

        # Store username for serialization
        self.username = username.strip()

        random_num, code = self._get_captcha_code()
        headers = _base_headers.copy()
        headers["X-Requested-With"] = "XMLHttpRequest"
        headers["Referer"] = "https://jywg.18.cn/Login?el=1&clear=&returl=%2fTrade%2fBuy"
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        url = _urls["login"]
        data = {
            "userId": username.strip(),
            "password": emt_trade_encrypt(password.strip()),
            "randNumber": random_num,
            "identifyCode": code,
            "duration": duration,
            "authCode": "",
            "type": "Z",
            "secInfo": "",
        }

        resp = self.session.post(url, headers=headers, data=data)
        self._check_resp(resp)

        try:
            logger.info(f"login success for {resp.json()}")
            validate_key = self._get_em_validate_key()
        except KeyError as e:
            logger.error(f"param data found exception:[{e}], [data={resp}]")
            validate_key = None

        # Check if login succeeded
        if validate_key is None:
            raise LoginFailedError(f"Login failed for user '{username}'. Please check username, password, and captcha.")
        return validate_key

    def _re_login(self) -> str:
        """Re-login after session expiration.

        Clears the cached validation key and performs a new login.

        Returns:
            Validation key string if login succeeds

        Raises:
            LoginFailedError: If re-login fails
        """
        logger.info("Session expired, attempting to re-login...")
        # Clear the cached validation key
        self._em_validate_key = ""
        # Re-login using stored username and environment variables
        validate_key = self.login(self.username)
        if validate_key is None:
            raise LoginFailedError("Re-login failed after session expiration")
        return validate_key

    def verify_session(self) -> bool:
        """Verify if the current session is still valid.

        Makes a lightweight API call to check session validity.

        Returns:
            True if session is valid, False otherwise.
        """
        if not self._em_validate_key:
            return False

        try:
            # Use a lightweight query to verify session
            resp = self._query_something("query_asset_and_pos")
            return resp is not None
        except (SessionExpiredError, EmAPIError, Exception):
            return False

    def query_abbrs(self, *keys: str) -> dict:
        """Query abbreviation mappings from abbrs.json.

        Args:
            *keys: One or more abbreviation keys to look up

        Returns:
            Dict containing the abbreviation data for the specified keys.
            If no keys provided, returns all abbreviations.
            If a key is not found, it will be omitted from the result.

        Example:
            >>> client.query_abbrs("Zqdm", "Zqmc")
            {"Zqdm": {...}, "Zqmc": {...}}
        """
        # Get the directory of this file to locate abbrs.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        abbrs_path = os.path.join(current_dir, "..", "..", "abbrs.json")

        with open(abbrs_path, "r", encoding="utf-8") as f:
            all_abbrs = json.load(f)

        if not keys:
            return all_abbrs

        return {k: all_abbrs[k] for k in keys if k in all_abbrs}

    def query_asset_and_position(self) -> Optional[dict]:
        """Get asset and position information.

        Returns:
            Dict containing asset and position data or None
        """
        resp = self._query_something_with_retry("query_asset_and_pos")
        if resp:
            return resp.json()
        return None

    def query_orders(self) -> Optional[dict]:
        """Query current orders.

        Returns:
            Dict containing orders data or None
        """
        resp = self._query_something_with_retry("query_orders")
        if resp:
            return resp.json()
        return None

    def query_trades(self) -> Optional[dict]:
        """Query executed trades.

        Returns:
            Dict containing trades data or None
        """
        resp = self._query_something_with_retry("query_trades")
        if resp:
            return resp.json()
        return None

    def query_history_orders(self, size: int, start_time: str, end_time: str) -> Optional[dict]:
        """Query historical orders.

        Args:
            size: Number of records to retrieve
            start_time: Start date in format "%Y-%m-%d"
            end_time: End date in format "%Y-%m-%d"

        Returns:
            Dict containing historical orders data or None
        """
        req_data = {"qqhs": size, "dwc": "", "st": start_time, "et": end_time}
        resp = self._query_something_with_retry("query_his_orders", req_data)
        if resp:
            return resp.json()
        return None

    def query_history_trades(self, size: int, start_time: str, end_time: str) -> Optional[dict]:
        """Query historical trades.

        Args:
            size: Number of records to retrieve
            start_time: Start date in format "%Y-%m-%d"
            end_time: End date in format "%Y-%m-%d"

        Returns:
            Dict containing historical trades data or None
        """
        req_data = {"qqhs": size, "dwc": "", "st": start_time, "et": end_time}
        resp = self._query_something_with_retry("query_his_trades", req_data)
        if resp:
            return resp.json()
        return None

    def query_funds_flow(self, size: int, start_time: str, end_time: str) -> Optional[dict]:
        """Query funds flow.

        Args:
            size: Number of records to retrieve
            start_time: Start date in format "%Y-%m-%d"
            end_time: End date in format "%Y-%m-%d"

        Returns:
            Dict containing funds flow data or None
        """
        req_data = {"qqhs": size, "dwc": "", "st": start_time, "et": end_time}
        resp = self._query_something_with_retry("query_funds_flow", req_data)
        if resp:
            return resp.json()
        return None

    def create_order(self, stock_code: str, trade_type: str, market: str, price: float, amount: int) -> Optional[dict]:
        """Create a buy or sell order.

        Args:
            stock_code: Stock code
            trade_type: Trade direction, 'B' for buy, 'S' for sell
            market: Market identifier (e.g., 'HA' for Shanghai, 'SA' for Shenzhen)
            price: Order price
            amount: Order quantity

        Returns:
            Dict containing order response or None
        """
        req_data = {
            "stockCode": stock_code,
            "tradeType": trade_type,
            "zqmc": "",
            "market": market,
            "price": price,
            "amount": amount,
        }
        resp = self._query_something_with_retry("create_order", req_data)
        if resp:
            logger.info(resp.json())
            return resp.json()
        return None

    def cancel_order(self, order_str: str) -> Optional[str]:
        """Cancel an order.

        Args:
            order_str: Order identifier combining date and order number.
                      Format: "20240520_130662" where Wtrq is the date and Wtbh is the order number.

        Returns:
            Response text or None
        """
        data = {"revokes": order_str.strip()}
        resp = self._query_something_with_retry("cancel_order", req_data=data)
        if resp:
            return resp.text.strip()
        return None
