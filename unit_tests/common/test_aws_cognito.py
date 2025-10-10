import pytest
import requests
from unittest.mock import patch, MagicMock
from jwt import ExpiredSignatureError, InvalidTokenError
from app.common.aws_cognito import CognitoClientHelper
from app.common.responses import UnauthorizedException


@pytest.fixture
def env():
    mock_env = MagicMock()
    mock_env.AWS_ACCESS_KEY = "test-access-key"
    mock_env.AWS_SECRET_ACCESS_KEY = "test-secret"
    mock_env.AWS_REGION = "us-west-2"
    mock_env.AWS_COGNITO_USER_POOL_ID = "us-west-2_123456"
    mock_env.AWS_COGNITO_APP_CLIENT_ID = "app-client-id"
    return mock_env


@pytest.fixture
def mock_boto3_client():
    with patch("app.common.aws_cognito.boto3.client") as mock_client:
        yield mock_client


@pytest.fixture
def helper(env, mock_boto3_client):
    return CognitoClientHelper(env)


@pytest.fixture(autouse=True)
def patch_jwk_to_pem(monkeypatch):
    # Always patch jwk_to_pem to return a dummy PEM for all tests
    monkeypatch.setattr(
        "app.common.aws_cognito.CognitoClientHelper.jwk_to_pem",
        lambda self, jwk: b"-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAn\n-----END PUBLIC KEY-----",
    )


@pytest.fixture
def mock_requests_get():
    with patch("app.common.aws_cognito.requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_jwt(monkeypatch):
    import app.common.aws_cognito as aws_cognito_mod

    monkeypatch.setattr(aws_cognito_mod.jwt, "get_unverified_header", MagicMock())
    monkeypatch.setattr(aws_cognito_mod.jwt, "decode", MagicMock())
    return aws_cognito_mod.jwt


def test_verify_id_token_success(
    helper, mock_boto3_client, mock_requests_get, mock_jwt
):
    # Setup JWKS and headers
    kid = "test-kid"
    jwk = {"kid": kid, "n": "AQAB", "e": "AQAB"}
    mock_requests_get.return_value.json.return_value = {"keys": [jwk]}
    mock_jwt.get_unverified_header.return_value = {"kid": kid}
    claims = {"sub": "user123", "email": "user@example.com"}
    mock_jwt.decode.return_value = claims

    # Setup Cognito user
    user_attributes = [{"Name": "email", "Value": "user@example.com"}]
    mock_boto3_client.return_value.admin_get_user.return_value = {
        "UserAttributes": user_attributes
    }

    # Should not raise
    result = helper.verify_id_token("user@example.com", "fake-token")
    assert result == "user@example.com"


def test_verify_id_token_email_mismatch(
    helper, mock_boto3_client, mock_requests_get, mock_jwt
):
    kid = "test-kid"
    jwk = {"kid": kid, "n": "AQAB", "e": "AQAB"}
    mock_requests_get.return_value.json.return_value = {"keys": [jwk]}
    mock_jwt.get_unverified_header.return_value = {"kid": kid}
    claims = {"sub": "user123", "email": "wrong@example.com"}
    mock_jwt.decode.return_value = claims
    user_attributes = [{"Name": "email", "Value": "user@example.com"}]
    mock_boto3_client.return_value.admin_get_user.return_value = {
        "UserAttributes": user_attributes
    }

    with pytest.raises(UnauthorizedException, match="Email does not match"):
        helper.verify_id_token("user@example.com", "fake-token")


def test_verify_id_token_user_not_found(
    helper, mock_boto3_client, mock_requests_get, mock_jwt
):
    kid = "test-kid"
    jwk = {"kid": kid, "n": "AQAB", "e": "AQAB"}
    mock_requests_get.return_value.json.return_value = {"keys": [jwk]}
    mock_jwt.get_unverified_header.return_value = {"kid": kid}
    claims = {"sub": "user123", "email": "user@example.com"}
    mock_jwt.decode.return_value = claims
    mock_boto3_client.return_value.admin_get_user.return_value = None

    with pytest.raises(UnauthorizedException, match="User does not exist"):
        helper.verify_id_token("user@example.com", "fake-token")


def test_verify_id_token_jwks_fetch_error(helper, mock_boto3_client, mock_requests_get):
    mock_requests_get.side_effect = requests.exceptions.RequestException(
        "Network error"
    )
    with pytest.raises(UnauthorizedException, match="Failed to fetch JWKS"):
        helper.verify_id_token("user@example.com", "fake-token")


def test_verify_id_token_expired_signature(
    helper, mock_boto3_client, mock_requests_get, mock_jwt
):
    kid = "test-kid"
    jwk = {"kid": kid, "n": "AQAB", "e": "AQAB"}
    mock_requests_get.return_value.json.return_value = {"keys": [jwk]}
    mock_jwt.get_unverified_header.return_value = {"kid": kid}

    mock_jwt.decode.side_effect = ExpiredSignatureError()
    with pytest.raises(UnauthorizedException, match="ID token has expired"):
        helper.verify_id_token("user@example.com", "fake-token")


def test_verify_id_token_invalid_token(
    helper, mock_boto3_client, mock_requests_get, mock_jwt
):
    kid = "test-kid"
    jwk = {"kid": kid, "n": "AQAB", "e": "AQAB"}
    mock_requests_get.return_value.json.return_value = {"keys": [jwk]}
    mock_jwt.get_unverified_header.return_value = {"kid": kid}

    mock_jwt.decode.side_effect = InvalidTokenError("bad token")
    with pytest.raises(UnauthorizedException, match="Invalid ID token: bad token"):
        helper.verify_id_token("user@example.com", "fake-token")
