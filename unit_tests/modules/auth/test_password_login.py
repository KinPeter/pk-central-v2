import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from app.modules.auth.password_login import password_login
from app.modules.auth.auth_types import LoginResponse, PasswordLoginRequest
from app.common.responses import InternalServerErrorException, UnauthorizedException


class TestPasswordLogin:
    @pytest.fixture
    def env(self):
        mock_env = MagicMock()
        mock_env.JWT_SECRET = "secret"
        mock_env.TOKEN_EXPIRY = 1
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

    @pytest.fixture
    def expires_at(self):
        return datetime.now() + timedelta(days=1)

    @pytest.mark.asyncio
    async def test_successful_login(self, request_obj, expires_at):
        email = "test@example.com"
        password = "password123"
        user = {
            "id": "user1",
            "email": email,
            "password_hash": "hash",
            "password_salt": "salt",
        }
        body = PasswordLoginRequest(email=email, password=password)
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=user)
        request_obj.app.state.db.get_collection.return_value = db_collection
        with patch(
            "app.modules.auth.password_login.verify_password", return_value=True
        ):
            with patch(
                "app.modules.auth.password_login.get_access_token",
                return_value=("token", expires_at),
            ):
                result = await password_login(body, request_obj)
                assert isinstance(result, LoginResponse)
                assert result.email == email
                assert result.id == user["id"]
                assert result.token == "token"
                assert result.expires_at == expires_at

    @pytest.mark.asyncio
    async def test_user_not_found(self, request_obj):
        body = PasswordLoginRequest(email="notfound@example.com", password="password")
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=None)
        request_obj.app.state.db.get_collection.return_value = db_collection
        with pytest.raises(UnauthorizedException):
            await password_login(body, request_obj)

    @pytest.mark.asyncio
    async def test_invalid_password(self, request_obj):
        email = "test@example.com"
        user = {
            "id": "user1",
            "email": email,
            "password_hash": "hash",
            "password_salt": "salt",
        }
        body = PasswordLoginRequest(email=email, password="wrongpassw")
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=user)
        request_obj.app.state.db.get_collection.return_value = db_collection
        with patch(
            "app.modules.auth.password_login.verify_password", return_value=False
        ):
            with pytest.raises(UnauthorizedException):
                await password_login(body, request_obj)

    @pytest.mark.asyncio
    async def test_db_error(self, request_obj):
        body = PasswordLoginRequest(email="test@example.com", password="password")
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(side_effect=Exception("db fail"))
        request_obj.app.state.db.get_collection.return_value = db_collection
        with pytest.raises(InternalServerErrorException):
            await password_login(body, request_obj)
            request_obj.app.state.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_token_generation_error(self, request_obj):
        email = "test@example.com"
        user = {
            "id": "user1",
            "email": email,
            "password_hash": "hash",
            "password_salt": "salt",
        }
        body = PasswordLoginRequest(email=email, password="password")
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=user)
        request_obj.app.state.db.get_collection.return_value = db_collection
        with patch(
            "app.modules.auth.password_login.verify_password", return_value=True
        ):
            with patch(
                "app.modules.auth.password_login.get_access_token",
                side_effect=Exception("fail"),
            ):
                with pytest.raises(InternalServerErrorException):
                    await password_login(body, request_obj)
                    request_obj.app.state.logger.error.assert_called()
