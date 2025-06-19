import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from app.modules.auth.set_password import set_password
from app.common.responses import (
    ForbiddenOperationException,
    InternalServerErrorException,
    IdResponse,
)
from app.modules.auth.auth_types import PasswordLoginRequest, CurrentUser


class TestSetPassword:
    @pytest.fixture
    def logger(self):
        return MagicMock()

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def request_obj(self, logger, db):
        mock_request = MagicMock(spec=Request)
        mock_request.app.state.logger = logger
        mock_request.app.state.db = db
        return mock_request

    @pytest.fixture
    def req_user(self):
        user = MagicMock()
        user.id = "user1"
        return user

    @pytest.mark.asyncio
    async def test_successful_set_password(self, request_obj, req_user):
        email = "test@example.com"
        password = "password123"
        body = PasswordLoginRequest(email=email, password=password)
        user = {"id": req_user.id, "email": email}
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=user)
        db_collection.update_one = AsyncMock()
        request_obj.app.state.db.get_collection.return_value = db_collection
        with patch(
            "app.modules.auth.set_password.get_hashed", return_value=("hash", "salt")
        ):
            result = await set_password(body, request_obj, req_user)
            assert isinstance(result, IdResponse)
            assert result.id == user["id"]
            db_collection.update_one.assert_awaited_once()
            request_obj.app.state.logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_user_not_found(self, request_obj, req_user):
        email = "test@example.com"
        body = PasswordLoginRequest(email=email, password="passwwww")
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=None)
        request_obj.app.state.db.get_collection.return_value = db_collection
        with pytest.raises(ForbiddenOperationException):
            await set_password(body, request_obj, req_user)

    @pytest.mark.asyncio
    async def test_email_mismatch(self, request_obj, req_user):
        email = "test@example.com"
        body = PasswordLoginRequest(email=email, password="password")
        user = {"id": req_user.id, "email": "other@example.com"}
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=user)
        request_obj.app.state.db.get_collection.return_value = db_collection
        with pytest.raises(ForbiddenOperationException):
            await set_password(body, request_obj, req_user)

    @pytest.mark.asyncio
    async def test_db_error(self, request_obj, req_user):
        email = "test@example.com"
        body = PasswordLoginRequest(email=email, password="password")
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(side_effect=Exception("db fail"))
        request_obj.app.state.db.get_collection.return_value = db_collection
        with pytest.raises(InternalServerErrorException):
            await set_password(body, request_obj, req_user)
            request_obj.app.state.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_update_error(self, request_obj, req_user):
        email = "test@example.com"
        body = PasswordLoginRequest(email=email, password="ppasswordw")
        user = {"id": req_user.id, "email": email}
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=user)
        db_collection.update_one = AsyncMock(side_effect=Exception("fail"))
        request_obj.app.state.db.get_collection.return_value = db_collection
        with patch(
            "app.modules.auth.set_password.get_hashed", return_value=("hash", "salt")
        ):
            with pytest.raises(InternalServerErrorException):
                await set_password(body, request_obj, req_user)
                request_obj.app.state.logger.error.assert_called()
