import base64
import logging

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa

rsa_public_key = """
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDHdsyxT66pDG4p73yope7jxA92
c0AT4qIJ/xtbBcHkFPK77upnsfDTJiVEuQDH+MiMeb+XhCLNKZGp0yaUU6GlxZdp
+nLW8b7Kmijr3iepaDhcbVTsYBWchaWUXauj9Lrhz58/6AE/NF0aMolxIGpsi+ST
2hSHPu3GSXMdhPCkWQIDAQAB
-----END PUBLIC KEY-----
"""


def get_logger(name: str) -> logging.Logger:
    """Configure and return a logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Configured logger instance
    """
    formater = "%(asctime)s %(name)-20s %(funcName)s %(lineno)d: %(levelname)-8s: %(message)s"
    logging.basicConfig(format=formater, force=True, level=logging.INFO)
    logger = logging.getLogger(name)
    return logger


def emt_trade_encrypt(content: str) -> str:
    """Encrypt content using RSA public key for EMT trading.

    Args:
        content: Plaintext content to encrypt

    Returns:
        Base64 encoded encrypted string
    """
    _pub_key: rsa.RSAPublicKey = serialization.load_pem_public_key(rsa_public_key.encode("utf-8"))  # type:ignore
    encrypt_text = _pub_key.encrypt(content.encode(), padding.PKCS1v15())
    return base64.b64encode(encrypt_text).decode("utf-8")


def get_float(data: dict, key: str) -> float:
    """Extract and convert string value to float from dict.

    Args:
        data: Dictionary containing the value
        key: Key to look up in the dictionary

    Returns:
        Float value or 0.0 if value is empty
    """
    if v := data[key].strip():
        return float(v)
    return 0.0


def get_int(data: dict, key: str) -> int:
    """Extract and convert string value to int from dict.

    Args:
        data: Dictionary containing the value
        key: Key to look up in the dictionary

    Returns:
        Integer value or 0 if value is empty
    """
    if v := data[key].strip():
        return int(v)
    return 0
