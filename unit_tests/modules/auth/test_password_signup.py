import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from app.modules.auth.password_signup import password_signup
from app.common.responses import (
    ConflictException,
    ForbiddenOperationException,
    InternalServerErrorException,
    IdResponse,
)
from app.modules.auth.auth_types import PasswordLoginRequest


class TestPasswordSignup:
    @pytest.fixture
    def env(self):
        mock_env = MagicMock()
        mock_env.PK_ENV = "dev"
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
    async def test_successful_signup(self, request_obj):
        email = "test@example.com"
        password = "password123"
        body = PasswordLoginRequest(email=email, password=password)
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=None)
        db_collection.update_one = AsyncMock()
        db_collection.find_one_and_delete = AsyncMock()
        request_obj.app.state.db.get_collection.return_value = db_collection
        with patch(
            "app.modules.auth.password_signup.EmailManager"
        ) as mock_email_manager:
            with patch(
                "app.modules.auth.password_signup.create_initial_user",
                new_callable=AsyncMock,
            ) as mock_create_user:
                mock_create_user.return_value = {"id": "user1", "email": email}
                with patch(
                    "app.modules.auth.password_signup.get_hashed",
                    return_value=("hash", "salt"),
                ):
                    result = await password_signup(body, request_obj)
                    assert isinstance(result, IdResponse)
                    assert result.id == "user1"
                    mock_create_user.assert_awaited_once_with(
                        email, request_obj.app.state.db, request_obj.app.state.logger
                    )
                    mock_email_manager.return_value.send_signup_notification.assert_called_once_with(
                        email
                    )
                    db_collection.update_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_conflict_existing_user(self, request_obj):
        email = "test@example.com"
        body = PasswordLoginRequest(email=email, password="password")
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value={"id": "user1", "email": email})
        request_obj.app.state.db.get_collection.return_value = db_collection
        with pytest.raises(ConflictException):
            await password_signup(body, request_obj)

    @pytest.mark.asyncio
    async def test_forbidden_email(self, request_obj):
        request_obj.app.state.env.EMAILS_ALLOWED = (
            "allowed@example.com,other@example.com"
        )
        email = "notallowed@example.com"
        body = PasswordLoginRequest(email=email, password="password")
        with pytest.raises(ForbiddenOperationException):
            await password_signup(body, request_obj)

    @pytest.mark.asyncio
    async def test_internal_server_error(self, request_obj):
        email = "test@example.com"
        password = "password123"
        body = PasswordLoginRequest(email=email, password=password)
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=None)
        db_collection.update_one = AsyncMock()
        db_collection.find_one_and_delete = AsyncMock()
        request_obj.app.state.db.get_collection.return_value = db_collection
        with patch("app.common.email.EmailManager") as mock_email_manager:
            with patch(
                "app.modules.auth.password_signup.create_initial_user",
                new_callable=AsyncMock,
            ) as mock_create_user:
                mock_create_user.return_value = {"id": "user1", "email": email}
                with patch(
                    "app.modules.auth.password_signup.get_hashed",
                    return_value=("hash", "salt"),
                ):
                    db_collection.update_one.side_effect = Exception("fail")
                    with pytest.raises(InternalServerErrorException):
                        await password_signup(body, request_obj)
                    db_collection.find_one_and_delete.assert_awaited_once()
                    request_obj.app.state.logger.error.assert_called()
