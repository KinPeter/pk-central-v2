import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from app.modules.auth.instant_login_code import instant_login_code
from app.modules.auth.auth_types import EmailLoginRequest, LoginCodeResponse
from app.common.responses import (
    ForbiddenOperationException,
    InternalServerErrorException,
)


class TestInstantLoginCode:
    @pytest.fixture
    def env(self):
        mock_env = MagicMock()
        mock_env.PK_ENV = "dev"
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
    async def test_successful_instant_login_code(self, request_obj):
        email = "test@example.com"
        body = EmailLoginRequest(email=email)
        with patch(
            "app.modules.auth.instant_login_code.sign_up_or_login_user",
            new_callable=AsyncMock,
        ) as mock_signup:
            mock_signup.return_value = "123456"
            result = await instant_login_code(body, request_obj)
            assert isinstance(result, LoginCodeResponse)
            assert result.login_code == "123456"
            request_obj.app.state.logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_forbidden_env(self, request_obj):
        request_obj.app.state.env.PK_ENV = "prod"
        body = EmailLoginRequest(email="test@example.com")
        with pytest.raises(ForbiddenOperationException):
            await instant_login_code(body, request_obj)

    @pytest.mark.asyncio
    async def test_internal_server_error(self, request_obj):
        email = "test@example.com"
        body = EmailLoginRequest(email=email)
        with patch(
            "app.modules.auth.instant_login_code.sign_up_or_login_user",
            new_callable=AsyncMock,
        ) as mock_signup:
            mock_signup.side_effect = Exception("fail")
            with pytest.raises(InternalServerErrorException):
                await instant_login_code(body, request_obj)
                request_obj.app.state.logger.error.assert_called()
