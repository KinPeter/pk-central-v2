import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from datetime import datetime, timedelta, timezone
from app.modules.auth.verify_login_code import login_code_verify
from app.modules.auth.auth_types import CodeLoginRequest, LoginResponse
from app.common.responses import InternalServerErrorException, UnauthorizedException


class TestVerifyLoginCode:
    @pytest.fixture
    def env(self):
        mock_env = MagicMock()
        mock_env.JWT_SECRET = "secret"
        mock_env.TOKEN_EXPIRY = 2
        return mock_env

    @pytest.fixture
    def logger(self):
        return MagicMock()

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def request_obj(self, env, logger, db):
        mock_request = MagicMock(spec=Request)
        mock_request.app.state.env = env
        mock_request.app.state.logger = logger
        mock_request.app.state.db = db
        return mock_request

    @pytest.mark.asyncio
    async def test_login_code_verify_success(self, request_obj):
        email = "test@example.com"
        login_code = "123456"
        body = CodeLoginRequest(email=email, login_code=login_code)
        user = {
            "id": "user1",
            "email": email,
            "login_code_hash": "hash",
            "login_code_salt": "salt",
            "login_code_expires": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        users_collection = AsyncMock()
        users_collection.find_one = AsyncMock(return_value=user)
        request_obj.app.state.db.get_collection.return_value = users_collection
        with patch(
            "app.modules.auth.verify_login_code.verify_login_code", return_value=True
        ), patch(
            "app.modules.auth.verify_login_code.get_access_token",
            return_value=("token", datetime.now(timezone.utc) + timedelta(days=2)),
        ):
            response = await login_code_verify(body, request_obj)
            assert isinstance(response, LoginResponse)
            assert response.email == email
            assert response.id == user["id"]
            assert response.token == "token"

    @pytest.mark.asyncio
    async def test_login_code_verify_user_not_found(self, request_obj):
        email = "notfound@example.com"
        login_code = "123456"
        body = CodeLoginRequest(email=email, login_code=login_code)
        users_collection = AsyncMock()
        users_collection.find_one = AsyncMock(return_value=None)
        request_obj.app.state.db.get_collection.return_value = users_collection
        with pytest.raises(UnauthorizedException):
            await login_code_verify(body, request_obj)

    @pytest.mark.asyncio
    async def test_login_code_verify_invalid_code(self, request_obj):
        email = "test@example.com"
        login_code = "badcode"
        body = CodeLoginRequest(email=email, login_code=login_code)
        user = {
            "id": "user1",
            "email": email,
            "login_code_hash": "hash",
            "login_code_salt": "salt",
            "login_code_expires": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        users_collection = AsyncMock()
        users_collection.find_one = AsyncMock(return_value=user)
        request_obj.app.state.db.get_collection.return_value = users_collection
        with patch(
            "app.modules.auth.verify_login_code.verify_login_code",
            side_effect=UnauthorizedException("Invalid login code"),
        ):
            with pytest.raises(UnauthorizedException):
                await login_code_verify(body, request_obj)

    @pytest.mark.asyncio
    async def test_login_code_verify_expired_code(self, request_obj):
        email = "test@example.com"
        login_code = "123456"
        body = CodeLoginRequest(email=email, login_code=login_code)
        user = {
            "id": "user1",
            "email": email,
            "login_code_hash": "hash",
            "login_code_salt": "salt",
            "login_code_expires": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        users_collection = AsyncMock()
        users_collection.find_one = AsyncMock(return_value=user)
        request_obj.app.state.db.get_collection.return_value = users_collection
        with patch(
            "app.modules.auth.verify_login_code.verify_login_code",
            side_effect=UnauthorizedException("Login code has expired"),
        ):
            with pytest.raises(UnauthorizedException):
                await login_code_verify(body, request_obj)

    @pytest.mark.asyncio
    async def test_login_code_verify_internal_error(self, request_obj):
        email = "test@example.com"
        login_code = "123456"
        body = CodeLoginRequest(email=email, login_code=login_code)
        users_collection = AsyncMock()
        users_collection.find_one = AsyncMock(side_effect=Exception("db error"))
        request_obj.app.state.db.get_collection.return_value = users_collection
        with pytest.raises(InternalServerErrorException):
            await login_code_verify(body, request_obj)
            request_obj.app.state.logger.error.assert_called()
