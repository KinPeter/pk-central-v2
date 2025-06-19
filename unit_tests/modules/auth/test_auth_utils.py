import pytest
import jwt
import re
import base64
import os
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.modules.auth.auth_utils import (
    get_access_token,
    get_hashed,
    verify_token,
    get_login_code,
    verify_login_code,
    verify_password,
)
from app.common.responses import UnauthorizedException


class TestGetAccessToken:
    @pytest.fixture
    def user_id(self):
        return "test-user-id"

    @pytest.fixture
    def secret(self):
        return "supersecret"

    def test_get_access_token_returns_token_and_expiry(self, user_id, secret):
        with patch("app.modules.auth.auth_utils.jwt.encode") as mock_encode:
            mock_encode.return_value = "mocked.jwt.token"
            token, expires_at = get_access_token(user_id, secret, 2)
            assert token == "mocked.jwt.token"
            assert isinstance(expires_at, datetime)
            assert expires_at.tzinfo == timezone.utc

            # Check payload passed to jwt.encode
            args, kwargs = mock_encode.call_args
            payload = args[0]
            assert payload["user_id"] == user_id
            assert "exp" in payload
            # exp should be about now + 2 days (in seconds)
            now = int(datetime.now(timezone.utc).timestamp())
            expected_exp = now + 2 * 24 * 60 * 60
            assert expected_exp - 5 <= payload["exp"] <= expected_exp + 5
            assert kwargs["key"] == secret
            assert kwargs["algorithm"] == "HS256"

    def test_get_access_token_accepts_str_days(self, user_id, secret):
        with patch("app.modules.auth.auth_utils.jwt.encode") as mock_encode:
            mock_encode.return_value = "mocked.jwt.token"
            token, expires_at = get_access_token(user_id, secret, "1")
            assert token == "mocked.jwt.token"
            assert isinstance(expires_at, datetime)
            assert expires_at.tzinfo == timezone.utc

            args, kwargs = mock_encode.call_args
            payload = args[0]
            assert payload["user_id"] == user_id
            assert "exp" in payload
            # exp should be about now + 1 day (in seconds)
            now = int(datetime.now(timezone.utc).timestamp())
            expected_exp = now + 1 * 24 * 60 * 60
            assert expected_exp - 5 <= payload["exp"] <= expected_exp + 5


class TestVerifyToken:
    @pytest.fixture
    def secret(self):
        return "supersecret"

    @pytest.fixture
    def token(self):
        return "sometoken"

    def test_verify_token_success(self, secret, token):
        payload = {"user_id": "test-user-id", "exp": 9999999999}
        with patch(
            "app.modules.auth.auth_utils.jwt.decode", return_value=payload
        ) as mock_decode:
            result = verify_token(token, secret)
            assert result == payload
            mock_decode.assert_called_once_with(token, secret, algorithms=["HS256"])

    def test_verify_token_expired(self, secret, token):
        with patch("app.modules.auth.auth_utils.jwt.decode") as mock_decode:
            mock_decode.side_effect = Exception("ExpiredSignatureError")
            with patch(
                "app.modules.auth.auth_utils.jwt.ExpiredSignatureError", Exception
            ):
                with pytest.raises(UnauthorizedException):
                    verify_token(token, secret)

    def test_verify_token_expired_real(self, secret):
        # Create a token that expired 1 second ago
        payload = {
            "user_id": "test-user-id",
            "exp": int((datetime.now(timezone.utc) - timedelta(seconds=1)).timestamp()),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        with pytest.raises(UnauthorizedException) as exc_info:
            verify_token(token, secret)
            assert "expired" in str(exc_info.value).lower()

    def test_verify_token_invalid(self, secret, token):
        with patch("app.modules.auth.auth_utils.jwt.decode") as mock_decode:
            mock_decode.side_effect = Exception("InvalidTokenError")
            with patch("app.modules.auth.auth_utils.jwt.InvalidTokenError", Exception):
                with pytest.raises(UnauthorizedException):
                    verify_token(token, secret)

    def test_verify_token_invalid_real(self, secret):
        # Create a token with an invalid signature
        payload = {"user_id": "test-user-id", "exp": 9999999999}
        wrong_secret = secret + "wrong"
        token = jwt.encode(payload, wrong_secret, algorithm="HS256")
        with pytest.raises(UnauthorizedException) as exc_info:
            verify_token(token, secret)
            assert "invalid" in str(exc_info.value).lower()


class TestGetLoginCode:
    def test_login_code_is_6_digits(self):
        with patch(
            "app.modules.auth.auth_utils.get_hashed", return_value=("hash", "salt")
        ):
            result = get_login_code(10)
            assert re.fullmatch(r"\d{6}", result.login_code)

    def test_expiry_is_correct(self):
        with patch(
            "app.modules.auth.auth_utils.get_hashed", return_value=("hash", "salt")
        ):
            minutes = 15
            before = datetime.now(timezone.utc) + timedelta(minutes=minutes)
            result = get_login_code(minutes)
            after = datetime.now(timezone.utc) + timedelta(minutes=minutes)
            assert before <= result.expiry <= after

    def test_hashed_and_salt_are_used(self):
        with patch(
            "app.modules.auth.auth_utils.get_hashed",
            return_value=("thehash", "thesalt"),
        ):
            result = get_login_code(5)
            assert result.hashed_login_code == "thehash"
            assert result.salt == "thesalt"

    def test_accepts_str_minutes(self):
        with patch(
            "app.modules.auth.auth_utils.get_hashed", return_value=("hash", "salt")
        ):
            result = get_login_code("20")
            assert isinstance(result.expiry, datetime)


class TestGetHashed:
    def test_returns_base64_strings(self):
        hash_b64, salt_b64 = get_hashed("password123")
        # Should be decodable from base64
        base64.b64decode(hash_b64)
        base64.b64decode(salt_b64)
        assert isinstance(hash_b64, str)
        assert isinstance(salt_b64, str)

    def test_salt_is_random(self):
        _, salt1 = get_hashed("abc")
        _, salt2 = get_hashed("abc")
        assert salt1 != salt2  # Salts should be different

    def test_hash_is_different_with_different_salts(self):
        hash1, salt1 = get_hashed("abc")
        hash2, salt2 = get_hashed("abc")
        assert hash1 != hash2  # Hashes should be different due to different salts

    def test_hash_is_same_with_same_salt(self):
        # Manually use the same salt to check determinism
        raw = "abc"
        salt = os.urandom(16)
        hash1 = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, 100_000)
        hash2 = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, 100_000)
        assert hash1 == hash2


class TestVerifyLoginCode:
    def test_valid_code_returns_true(self):
        raw_code = "123456"
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256", raw_code.encode("utf-8"), salt_bytes, 100_000
        )
        hashed_code = base64.b64encode(hash_bytes).decode("utf-8")
        expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
        assert verify_login_code(raw_code, hashed_code, salt, expiry) is True

    def test_expired_code_raises(self):
        raw_code = "123456"
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256", raw_code.encode("utf-8"), salt_bytes, 100_000
        )
        hashed_code = base64.b64encode(hash_bytes).decode("utf-8")
        expiry = datetime.now(timezone.utc) - timedelta(minutes=1)
        with pytest.raises(UnauthorizedException) as exc_info:
            verify_login_code(raw_code, hashed_code, salt, expiry)
        assert "expired" in str(exc_info.value).lower()

    def test_invalid_code_raises(self):
        raw_code = "123456"
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
        # Use a different code to generate the hash
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
        hash_bytes = hashlib.pbkdf2_hmac("sha256", b"654321", salt_bytes, 100_000)
        hashed_code = base64.b64encode(hash_bytes).decode("utf-8")
        expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
        with pytest.raises(UnauthorizedException) as exc_info:
            verify_login_code(raw_code, hashed_code, salt, expiry)
        assert "invalid" in str(exc_info.value).lower()


class TestVerifyPassword:
    def test_valid_password_returns_true(self):
        raw_password = "mysecret"
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256", raw_password.encode("utf-8"), salt_bytes, 100_000
        )
        hashed_password = base64.b64encode(hash_bytes).decode("utf-8")
        assert verify_password(raw_password, hashed_password, salt) is True

    def test_invalid_password_raises(self):
        raw_password = "mysecret"
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
        # Use a different password to generate the hash
        hash_bytes = hashlib.pbkdf2_hmac("sha256", b"notmysecret", salt_bytes, 100_000)
        hashed_password = base64.b64encode(hash_bytes).decode("utf-8")
        with pytest.raises(UnauthorizedException) as exc_info:
            verify_password(raw_password, hashed_password, salt)
        assert "invalid" in str(exc_info.value).lower()

    def test_empty_password_raises(self):
        raw_password = ""
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
        hash_bytes = hashlib.pbkdf2_hmac("sha256", b"something", salt_bytes, 100_000)
        hashed_password = base64.b64encode(hash_bytes).decode("utf-8")
        with pytest.raises(UnauthorizedException):
            verify_password(raw_password, hashed_password, salt)
