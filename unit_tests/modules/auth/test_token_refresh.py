import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from datetime import datetime, timedelta
from app.modules.auth.token_refresh import token_refresh
from app.modules.auth.auth_types import CurrentUser, LoginResponse
from app.common.responses import InternalServerErrorException


class TestTokenRefresh:
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
    def request_obj(self, env, logger):
        mock_request = MagicMock(spec=Request)
        mock_request.app.state.env = env
        mock_request.app.state.logger = logger
        return mock_request

    @pytest.fixture
    def user(self):
        return CurrentUser(id="user1", email="test@example.com")

    @pytest.mark.asyncio
    async def test_token_refresh_success(self, request_obj, user):
        token = "jwt.token"
        expires_at = datetime.now() + timedelta(days=2)
        with patch(
            "app.modules.auth.token_refresh.get_access_token"
        ) as mock_get_access_token:
            mock_get_access_token.return_value = (token, expires_at)
            response = await token_refresh(request_obj, user)
            assert isinstance(response, LoginResponse)
            assert response.token == token
            assert response.expires_at == expires_at.isoformat()
            assert response.email == user.email
            assert response.id == user.id
            mock_get_access_token.assert_called_once_with(
                user_id=user.id,
                secret=request_obj.app.state.env.JWT_SECRET,
                expires_in_days=request_obj.app.state.env.TOKEN_EXPIRY,
            )

    @pytest.mark.asyncio
    async def test_token_refresh_error(self, request_obj, user):
        with patch(
            "app.modules.auth.token_refresh.get_access_token"
        ) as mock_get_access_token:
            mock_get_access_token.side_effect = Exception("fail")
            with pytest.raises(InternalServerErrorException):
                await token_refresh(request_obj, user)
                request_obj.app.state.logger.error.assert_called()
