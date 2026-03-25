import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request

from app.modules.auth.generate_api_key import generate_api_key
from app.modules.auth.auth_types import CurrentUser, GenerateApiKeyRequest, GenerateApiKeyResponse
from app.common.responses import InternalServerErrorException


class TestGenerateApiKey:
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
    def user(self):
        return CurrentUser(id="user-123", email="test@example.com")

    @pytest.fixture
    def body(self):
        return GenerateApiKeyRequest(name="Home server")

    @pytest.mark.asyncio
    async def test_returns_generate_api_key_response(self, request_obj, user, body):
        db_collection = AsyncMock()
        db_collection.insert_one = AsyncMock()
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.generate_api_key.generate_api_key_data",
            return_value=("pk_rawkey123", "hexhash123"),
        ):
            result = await generate_api_key(body, request_obj, user)

        assert isinstance(result, GenerateApiKeyResponse)

    @pytest.mark.asyncio
    async def test_returns_raw_key_in_response(self, request_obj, user, body):
        db_collection = AsyncMock()
        db_collection.insert_one = AsyncMock()
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.generate_api_key.generate_api_key_data",
            return_value=("pk_rawkey123", "hexhash123"),
        ):
            result = await generate_api_key(body, request_obj, user)

        assert result.api_key == "pk_rawkey123"

    @pytest.mark.asyncio
    async def test_response_includes_key_id(self, request_obj, user, body):
        db_collection = AsyncMock()
        db_collection.insert_one = AsyncMock()
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.generate_api_key.generate_api_key_data",
            return_value=("pk_rawkey123", "hexhash123"),
        ):
            result = await generate_api_key(body, request_obj, user)

        assert result.id is not None
        assert len(result.id) > 0

    @pytest.mark.asyncio
    async def test_inserts_correct_document_into_db(self, request_obj, user, body):
        db_collection = AsyncMock()
        db_collection.insert_one = AsyncMock()
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.generate_api_key.generate_api_key_data",
            return_value=("pk_rawkey123", "hexhash123"),
        ):
            result = await generate_api_key(body, request_obj, user)

        db_collection.insert_one.assert_awaited_once()
        inserted_doc = db_collection.insert_one.call_args[0][0]
        assert inserted_doc["user_id"] == user.id
        assert inserted_doc["name"] == body.name
        assert inserted_doc["hashed_key"] == "hexhash123"
        assert inserted_doc["id"] == result.id
        assert inserted_doc["last_used_at"] is None
        assert "created_at" in inserted_doc

    @pytest.mark.asyncio
    async def test_hashed_key_is_stored_not_raw_key(self, request_obj, user, body):
        db_collection = AsyncMock()
        db_collection.insert_one = AsyncMock()
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.generate_api_key.generate_api_key_data",
            return_value=("pk_rawkey123", "hexhash123"),
        ):
            await generate_api_key(body, request_obj, user)

        inserted_doc = db_collection.insert_one.call_args[0][0]
        assert "pk_rawkey123" not in inserted_doc.values()
        assert inserted_doc["hashed_key"] == "hexhash123"

    @pytest.mark.asyncio
    async def test_logs_info_on_success(self, request_obj, user, body):
        db_collection = AsyncMock()
        db_collection.insert_one = AsyncMock()
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.generate_api_key.generate_api_key_data",
            return_value=("pk_rawkey123", "hexhash123"),
        ):
            await generate_api_key(body, request_obj, user)

        request_obj.app.state.logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_raises_internal_server_error_on_db_failure(self, request_obj, user, body):
        db_collection = AsyncMock()
        db_collection.insert_one = AsyncMock(side_effect=Exception("db error"))
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.generate_api_key.generate_api_key_data",
            return_value=("pk_rawkey123", "hexhash123"),
        ):
            with pytest.raises(InternalServerErrorException):
                await generate_api_key(body, request_obj, user)

        request_obj.app.state.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_raises_internal_server_error_on_key_generation_failure(
        self, request_obj, user, body
    ):
        with patch(
            "app.modules.auth.generate_api_key.generate_api_key_data",
            side_effect=Exception("rng failure"),
        ):
            with pytest.raises(InternalServerErrorException):
                await generate_api_key(body, request_obj, user)
