import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from app.modules.auth.request_login_code import request_login_code
from app.common.responses import (
    ForbiddenOperationException,
    InternalServerErrorException,
    MessageResponse,
)
from app.modules.auth.auth_types import EmailLoginRequest


class TestRequestLoginCode:
    @pytest.fixture
    def env(self):
        mock_env = MagicMock()
        mock_env.EMAILS_ALLOWED = "all"
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
    async def test_successful_request(self, request_obj):
        email = "test@example.com"
        body = EmailLoginRequest(email=email)
        with patch("app.common.email.EmailManager") as mock_email_manager:
            with patch(
                "app.modules.auth.request_login_code.sign_up_or_login_user",
                new_callable=AsyncMock,
            ) as mock_signup:
                mock_signup.return_value = None
                result = await request_login_code(body, request_obj)
                assert isinstance(result, MessageResponse)
                assert result.message == "Check your inbox"
                mock_signup.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_forbidden_email(self, request_obj):
        request_obj.app.state.env.EMAILS_ALLOWED = (
            "allowed@example.com, other@example.com"
        )
        email = "notallowed@example.com"
        body = EmailLoginRequest(email=email)
        with pytest.raises(ForbiddenOperationException):
            await request_login_code(body, request_obj)

    @pytest.mark.asyncio
    async def test_internal_server_error(self, request_obj):
        email = "test@example.com"
        body = EmailLoginRequest(email=email)
        with patch("app.common.email.EmailManager") as MockEmailManager:
            with patch(
                "app.modules.auth.request_login_code.sign_up_or_login_user",
                new_callable=AsyncMock,
            ) as mock_signup:
                mock_signup.side_effect = Exception("fail")
                with pytest.raises(InternalServerErrorException):
                    await request_login_code(body, request_obj)
                request_obj.app.state.logger.error.assert_called()
