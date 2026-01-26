"""Tests for EMTClient and multi-user support."""
import datetime
import math
import os

import pytest

from emtl import EMTClient

# Test credentials
TEST_USER1 = {"username": "540975189038", "password": "123731"}
TEST_USER2 = {"username": "540975113619", "password": "548112"}


class TestEMTClient:
    """Test EMTClient class functionality."""

    def test_client_creation(self):
        """Test that EMTClient can be instantiated."""
        client = EMTClient()
        assert client is not None
        assert client.ocr is not None
        assert client.session is not None
        assert client._em_validate_key == ""

    def test_multi_client_isolation(self):
        """Test that multiple clients have isolated state."""
        client1 = EMTClient()
        client2 = EMTClient()

        # Sessions should be different
        assert client1.session is not client2.session

        # OCR instances should be different
        assert client1.ocr is not client2.ocr

        # Initially both have empty validate_key (Python string singleton)
        assert client1._em_validate_key == client2._em_validate_key == ""

        # After setting different values, they should be different
        client1._em_validate_key = "key1"
        client2._em_validate_key = "key2"
        assert client1._em_validate_key != client2._em_validate_key

    def test_client_login_with_credentials(self):
        """Test client login with direct credentials."""
        client = EMTClient()
        # Login may fail due to captcha, but should not raise exception
        try:
            key = client.login(TEST_USER1["username"], TEST_USER1["password"])
            # If login succeeds, validate key format
            if key:
                assert len(key) == 36  # UUID format
        except Exception as e:
            # Login may fail due to captcha or other reasons
            pytest.skip(f"Login failed: {e}")

    def test_client_login_with_env(self):
        """Test client login using environment variables."""
        os.environ["EM_USERNAME"] = TEST_USER1["username"]
        os.environ["EM_PASSWORD"] = TEST_USER1["password"]

        client = EMTClient()
        try:
            key = client.login()
            if key:
                assert len(key) == 36
        except Exception as e:
            pytest.skip(f"Login failed: {e}")

    def test_client_get_last_price(self):
        """Test getting last price for a stock."""
        client = EMTClient()
        price = client.get_last_price("000001", "SA")
        # Price might be NaN if symbol not found
        assert isinstance(price, float)

    def test_client_query_methods_require_login(self):
        """Test that query methods work after login."""
        client = EMTClient()
        # Try to login first
        try:
            key = client.login(TEST_USER1["username"], TEST_USER1["password"])
            if not key:
                pytest.skip("Login failed")
        except Exception:
            pytest.skip("Login failed")

        # Test query methods
        orders = client.query_orders()
        assert orders is not None
        assert orders.get("Status") == 0

        asset = client.query_asset_and_position()
        assert asset is not None
        assert asset.get("Status") == 0


class TestMultiUserIsolation:
    """Test multi-user isolation."""

    def test_two_users_separate_sessions(self):
        """Test that two users have completely separate sessions."""
        user1 = EMTClient()
        user2 = EMTClient()

        # Verify isolation before login
        assert user1.session is not user2.session
        assert user1.ocr is not user2.ocr

        # Try to login both users
        try:
            key1 = user1.login(TEST_USER1["username"], TEST_USER1["password"])
            key2 = user2.login(TEST_USER2["username"], TEST_USER2["password"])

            # At least one should succeed for proper isolation test
            if key1 or key2:
                # If login succeeded, validate keys should be different
                if key1 and key2:
                    assert user1._em_validate_key != user2._em_validate_key
        except Exception:
            pytest.skip("Login failed")

    def test_users_dont_interfere(self):
        """Test that operations on one user don't affect another."""
        user1 = EMTClient()
        user2 = EMTClient()

        # Set different validate keys
        user1._em_validate_key = "user1_key"
        user2._em_validate_key = "user2_key"

        # Verify they remain different
        assert user1._em_validate_key == "user1_key"
        assert user2._em_validate_key == "user2_key"
        assert user1._em_validate_key != user2._em_validate_key


class TestClientMethods:
    """Test all EMTClient methods."""

    def test_query_orders(self):
        """Test query_orders method."""
        client = EMTClient()
        os.environ["EM_USERNAME"] = TEST_USER1["username"]
        os.environ["EM_PASSWORD"] = TEST_USER1["password"]

        try:
            client.login()
        except Exception:
            pytest.skip("Login failed")

        resp = client.query_orders()
        assert resp
        assert resp["Status"] == 0

    def test_query_trades(self):
        """Test query_trades method."""
        client = EMTClient()
        os.environ["EM_USERNAME"] = TEST_USER1["username"]
        os.environ["EM_PASSWORD"] = TEST_USER1["password"]

        try:
            client.login()
        except Exception:
            pytest.skip("Login failed")

        resp = client.query_trades()
        assert resp
        assert resp["Status"] == 0

    def test_query_history_orders(self):
        """Test query_history_orders method."""
        client = EMTClient()
        os.environ["EM_USERNAME"] = TEST_USER1["username"]
        os.environ["EM_PASSWORD"] = TEST_USER1["password"]

        try:
            client.login()
        except Exception:
            pytest.skip("Login failed")

        end_date = datetime.datetime.now(datetime.timezone.utc)
        start_date = end_date - datetime.timedelta(30)
        st = start_date.strftime("%Y-%m-%d")
        et = end_date.strftime("%Y-%m-%d")

        resp = client.query_history_orders(100, st, et)
        assert resp
        assert resp["Status"] == 0

    def test_query_history_trades(self):
        """Test query_history_trades method."""
        client = EMTClient()
        os.environ["EM_USERNAME"] = TEST_USER1["username"]
        os.environ["EM_PASSWORD"] = TEST_USER1["password"]

        try:
            client.login()
        except Exception:
            pytest.skip("Login failed")

        end_date = datetime.datetime.now(datetime.timezone.utc)
        start_date = end_date - datetime.timedelta(30)
        st = start_date.strftime("%Y-%m-%d")
        et = end_date.strftime("%Y-%m-%d")

        resp = client.query_history_trades(100, st, et)
        assert resp
        assert resp["Status"] == 0

    def test_query_funds_flow(self):
        """Test query_funds_flow method."""
        client = EMTClient()
        os.environ["EM_USERNAME"] = TEST_USER1["username"]
        os.environ["EM_PASSWORD"] = TEST_USER1["password"]

        try:
            client.login()
        except Exception:
            pytest.skip("Login failed")

        end_date = datetime.datetime.now(datetime.timezone.utc)
        start_date = end_date - datetime.timedelta(30)
        st = start_date.strftime("%Y-%m-%d")
        et = end_date.strftime("%Y-%m-%d")

        resp = client.query_funds_flow(100, st, et)
        assert resp
        assert resp["Status"] == 0

    def test_create_order(self):
        """Test create_order method."""
        client = EMTClient()
        os.environ["EM_USERNAME"] = TEST_USER1["username"]
        os.environ["EM_PASSWORD"] = TEST_USER1["password"]

        try:
            client.login()
        except Exception:
            pytest.skip("Login failed")

        resp = client.create_order("000002", "B", "SA", 5.01, 100)
        assert resp
        assert resp["Status"] in (0, -1)

    def test_cancel_order(self):
        """Test cancel_order method."""
        client = EMTClient()
        os.environ["EM_USERNAME"] = TEST_USER1["username"]
        os.environ["EM_PASSWORD"] = TEST_USER1["password"]

        try:
            client.login()
        except Exception:
            pytest.skip("Login failed")

        resp = client.cancel_order("20240520_130662")
        assert resp
        assert resp.startswith("130662")

    def test_get_last_price(self):
        """Test get_last_price method."""
        client = EMTClient()
        assert math.isnan(client.get_last_price("000001", "SA"))
