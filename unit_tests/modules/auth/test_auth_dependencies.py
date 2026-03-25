import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials

from app.modules.auth.auth_utils import auth_user, auth_api_key, auth_user_or_api_key
from app.modules.auth.auth_types import CurrentUser
from app.common.responses import InternalServerErrorException, UnauthorizedException


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def logger():
    return MagicMock()


@pytest.fixture
def env():
    mock_env = MagicMock()
    mock_env.JWT_SECRET = "test-secret"
    return mock_env


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
def user_doc():
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def credentials():
    mock = MagicMock(spec=HTTPAuthorizationCredentials)
    mock.credentials = "valid.jwt.token"
    return mock


# ---------------------------------------------------------------------------
# TestAuthUser
# ---------------------------------------------------------------------------


class TestAuthUser:
    @pytest.mark.asyncio
    async def test_valid_token_returns_current_user(
        self, request_obj, credentials, user_doc
    ):
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=user_doc)
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.auth_utils.verify_token", return_value="user-123"
        ):
            result = await auth_user(request_obj, credentials)

        assert isinstance(result, CurrentUser)
        assert result.id == "user-123"
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_invalid_token_raises_unauthorized(self, request_obj, credentials):
        with patch(
            "app.modules.auth.auth_utils.verify_token",
            side_effect=UnauthorizedException(reason="Invalid token"),
        ):
            with pytest.raises(UnauthorizedException):
                await auth_user(request_obj, credentials)

    @pytest.mark.asyncio
    async def test_user_not_found_raises_unauthorized(
        self, request_obj, credentials
    ):
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=None)
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.auth_utils.verify_token", return_value="user-123"
        ):
            with pytest.raises(UnauthorizedException):
                await auth_user(request_obj, credentials)

    @pytest.mark.asyncio
    async def test_db_error_raises_internal_server_error(
        self, request_obj, credentials
    ):
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(side_effect=Exception("db failure"))
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.auth_utils.verify_token", return_value="user-123"
        ):
            with pytest.raises(InternalServerErrorException):
                await auth_user(request_obj, credentials)

        request_obj.app.state.logger.error.assert_called()


# ---------------------------------------------------------------------------
# TestAuthApiKey
# ---------------------------------------------------------------------------


class TestAuthApiKey:
    @pytest.fixture
    def raw_api_key(self):
        return "pk_test_key_abc123"

    @pytest.fixture
    def api_key_doc(self, raw_api_key):
        return {
            "id": "key-doc-id",
            "user_id": "user-123",
            "hashed_key": hashlib.sha256(raw_api_key.encode()).hexdigest(),
        }

    @pytest.mark.asyncio
    async def test_valid_key_returns_current_user(
        self, request_obj, raw_api_key, api_key_doc, user_doc
    ):
        api_keys_collection = AsyncMock()
        api_keys_collection.find_one = AsyncMock(return_value=api_key_doc)
        api_keys_collection.update_one = AsyncMock()

        users_collection = AsyncMock()
        users_collection.find_one = AsyncMock(return_value=user_doc)

        def get_collection(name):
            if name == "api_keys":
                return api_keys_collection
            return users_collection

        request_obj.app.state.db.get_collection.side_effect = get_collection

        result = await auth_api_key(request_obj, raw_api_key)

        assert isinstance(result, CurrentUser)
        assert result.id == "user-123"
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_valid_key_updates_last_used_at(
        self, request_obj, raw_api_key, api_key_doc, user_doc
    ):
        api_keys_collection = AsyncMock()
        api_keys_collection.find_one = AsyncMock(return_value=api_key_doc)
        api_keys_collection.update_one = AsyncMock()

        users_collection = AsyncMock()
        users_collection.find_one = AsyncMock(return_value=user_doc)

        def get_collection(name):
            if name == "api_keys":
                return api_keys_collection
            return users_collection

        request_obj.app.state.db.get_collection.side_effect = get_collection

        await auth_api_key(request_obj, raw_api_key)

        api_keys_collection.update_one.assert_awaited_once()
        update_args = api_keys_collection.update_one.call_args[0]
        assert "last_used_at" in update_args[1]["$set"]

    @pytest.mark.asyncio
    async def test_invalid_key_raises_unauthorized(self, request_obj):
        api_keys_collection = AsyncMock()
        api_keys_collection.find_one = AsyncMock(return_value=None)
        request_obj.app.state.db.get_collection.return_value = api_keys_collection

        with pytest.raises(UnauthorizedException) as exc_info:
            await auth_api_key(request_obj, "pk_wrong_key")
        assert "Invalid API key" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_db_lookup_error_raises_internal_server_error(self, request_obj):
        api_keys_collection = AsyncMock()
        api_keys_collection.find_one = AsyncMock(side_effect=Exception("db failure"))
        request_obj.app.state.db.get_collection.return_value = api_keys_collection

        with pytest.raises(InternalServerErrorException):
            await auth_api_key(request_obj, "pk_some_key")

        request_obj.app.state.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_last_used_at_update_failure_does_not_raise(
        self, request_obj, raw_api_key, api_key_doc, user_doc
    ):
        api_keys_collection = AsyncMock()
        api_keys_collection.find_one = AsyncMock(return_value=api_key_doc)
        api_keys_collection.update_one = AsyncMock(side_effect=Exception("write fail"))

        users_collection = AsyncMock()
        users_collection.find_one = AsyncMock(return_value=user_doc)

        def get_collection(name):
            if name == "api_keys":
                return api_keys_collection
            return users_collection

        request_obj.app.state.db.get_collection.side_effect = get_collection

        # Should succeed despite update_one failing
        result = await auth_api_key(request_obj, raw_api_key)

        assert isinstance(result, CurrentUser)
        request_obj.app.state.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_user_not_found_raises_unauthorized(
        self, request_obj, raw_api_key, api_key_doc
    ):
        api_keys_collection = AsyncMock()
        api_keys_collection.find_one = AsyncMock(return_value=api_key_doc)
        api_keys_collection.update_one = AsyncMock()

        users_collection = AsyncMock()
        users_collection.find_one = AsyncMock(return_value=None)

        def get_collection(name):
            if name == "api_keys":
                return api_keys_collection
            return users_collection

        request_obj.app.state.db.get_collection.side_effect = get_collection

        with pytest.raises(UnauthorizedException):
            await auth_api_key(request_obj, raw_api_key)


# ---------------------------------------------------------------------------
# TestAuthUserOrApiKey
# ---------------------------------------------------------------------------


class TestAuthUserOrApiKey:
    @pytest.fixture
    def raw_api_key(self):
        return "pk_test_key_abc123"

    @pytest.mark.asyncio
    async def test_api_key_takes_priority_over_jwt(
        self, request_obj, credentials, raw_api_key
    ):
        with patch(
            "app.modules.auth.auth_utils.auth_api_key",
            new_callable=AsyncMock,
            return_value=CurrentUser(id="user-from-key", email="key@example.com"),
        ) as mock_api_key:
            result = await auth_user_or_api_key(
                request_obj, credentials=credentials, api_key=raw_api_key
            )

        assert result.id == "user-from-key"
        mock_api_key.assert_awaited_once_with(request_obj, raw_api_key)

    @pytest.mark.asyncio
    async def test_jwt_used_when_no_api_key(self, request_obj, credentials, user_doc):
        db_collection = AsyncMock()
        db_collection.find_one = AsyncMock(return_value=user_doc)
        request_obj.app.state.db.get_collection.return_value = db_collection

        with patch(
            "app.modules.auth.auth_utils.verify_token", return_value="user-123"
        ):
            result = await auth_user_or_api_key(
                request_obj, credentials=credentials, api_key=None
            )

        assert isinstance(result, CurrentUser)
        assert result.id == "user-123"

    @pytest.mark.asyncio
    async def test_no_credentials_raises_unauthorized(self, request_obj):
        with pytest.raises(UnauthorizedException) as exc_info:
            await auth_user_or_api_key(
                request_obj, credentials=None, api_key=None
            )
        assert "Authentication required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_unauthorized(
        self, request_obj, raw_api_key
    ):
        with patch(
            "app.modules.auth.auth_utils.auth_api_key",
            new_callable=AsyncMock,
            side_effect=UnauthorizedException(reason="Invalid API key"),
        ):
            with pytest.raises(UnauthorizedException):
                await auth_user_or_api_key(
                    request_obj, credentials=None, api_key=raw_api_key
                )

    @pytest.mark.asyncio
    async def test_invalid_jwt_raises_unauthorized(self, request_obj, credentials):
        with patch(
            "app.modules.auth.auth_utils.verify_token",
            side_effect=UnauthorizedException(reason="Token has expired"),
        ):
            with pytest.raises(UnauthorizedException):
                await auth_user_or_api_key(
                    request_obj, credentials=credentials, api_key=None
                )
