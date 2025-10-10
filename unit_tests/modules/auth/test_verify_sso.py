import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from datetime import datetime, timedelta
from app.modules.auth.verify_sso import sso_verify
from app.modules.auth.auth_types import SsoLoginRequest, LoginResponse
from app.common.responses import InternalServerErrorException, UnauthorizedException


# Fixtures for test setup
@pytest.fixture
def env():
    mock_env = MagicMock()
    mock_env.JWT_SECRET = "secret"
    mock_env.TOKEN_EXPIRY = 2
    return mock_env


@pytest.fixture
def logger():
    return MagicMock()


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def request_obj(env, logger, db):
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.env = env
    mock_request.app.state.logger = logger
    mock_request.app.state.db = db
    return mock_request


@pytest.fixture
def mock_cognito_helper():
    with patch("app.modules.auth.verify_sso.CognitoClientHelper") as MockCognito:
        yield MockCognito


@pytest.mark.asyncio
async def test_sso_verify_success(request_obj, mock_cognito_helper):
    email = "test@example.com"
    id_token = "idtoken123"
    body = SsoLoginRequest(email=email, id_token=id_token)
    user = {
        "id": "user1",
        "email": email,
    }
    users_collection = AsyncMock()
    users_collection.find_one = AsyncMock(return_value=user)
    request_obj.app.state.db.get_collection.return_value = users_collection
    expires_at = datetime.now() + timedelta(days=2)
    mock_cognito = mock_cognito_helper.return_value
    mock_cognito.verify_id_token.return_value = email
    with patch(
        "app.modules.auth.verify_sso.get_access_token",
        return_value=("token", expires_at),
    ):
        result = await sso_verify(body, request_obj)
        assert isinstance(result, LoginResponse)
        assert result.email == email
        assert result.id == user["id"]
        assert result.token == "token"
        assert result.expires_at == expires_at.isoformat()
    mock_cognito.verify_id_token.assert_called_once_with(email, id_token)


@pytest.mark.asyncio
async def test_sso_verify_user_not_found(request_obj, mock_cognito_helper):
    email = "notfound@example.com"
    id_token = "idtoken123"
    body = SsoLoginRequest(email=email, id_token=id_token)
    users_collection = AsyncMock()
    users_collection.find_one = AsyncMock(return_value=None)
    request_obj.app.state.db.get_collection.return_value = users_collection
    mock_cognito = mock_cognito_helper.return_value
    mock_cognito.verify_id_token.return_value = email
    with pytest.raises(UnauthorizedException, match="User does not exist"):
        await sso_verify(body, request_obj)
    mock_cognito.verify_id_token.assert_called_once_with(email, id_token)


@pytest.mark.asyncio
async def test_sso_verify_invalid_token(request_obj, mock_cognito_helper):
    email = "test@example.com"
    id_token = "badtoken"
    body = SsoLoginRequest(email=email, id_token=id_token)
    mock_cognito = mock_cognito_helper.return_value
    mock_cognito.verify_id_token.side_effect = UnauthorizedException("Invalid token")
    with pytest.raises(UnauthorizedException, match="Invalid token"):
        await sso_verify(body, request_obj)
    mock_cognito.verify_id_token.assert_called_once_with(email, id_token)


@pytest.mark.asyncio
async def test_sso_verify_db_error(request_obj, mock_cognito_helper):
    email = "test@example.com"
    id_token = "idtoken123"
    body = SsoLoginRequest(email=email, id_token=id_token)
    users_collection = AsyncMock()
    users_collection.find_one = AsyncMock(side_effect=Exception("db error"))
    request_obj.app.state.db.get_collection.return_value = users_collection
    mock_cognito = mock_cognito_helper.return_value
    mock_cognito.verify_id_token.return_value = email
    with pytest.raises(
        InternalServerErrorException,
        match="An error occurred while logging in. Please try again later.*db error",
    ):
        await sso_verify(body, request_obj)
    mock_cognito.verify_id_token.assert_called_once_with(email, id_token)
    request_obj.app.state.logger.error.assert_called()


@pytest.mark.asyncio
async def test_sso_verify_token_generation_error(request_obj, mock_cognito_helper):
    email = "test@example.com"
    id_token = "idtoken123"
    body = SsoLoginRequest(email=email, id_token=id_token)
    user = {
        "id": "user1",
        "email": email,
    }
    users_collection = AsyncMock()
    users_collection.find_one = AsyncMock(return_value=user)
    request_obj.app.state.db.get_collection.return_value = users_collection
    mock_cognito = mock_cognito_helper.return_value
    mock_cognito.verify_id_token.return_value = email
    with patch(
        "app.modules.auth.verify_sso.get_access_token",
        side_effect=Exception("fail"),
    ):
        with pytest.raises(
            InternalServerErrorException,
            match="An error occurred while logging in. Please try again later.*fail",
        ):
            await sso_verify(body, request_obj)
    mock_cognito.verify_id_token.assert_called_once_with(email, id_token)
    request_obj.app.state.logger.error.assert_called()
