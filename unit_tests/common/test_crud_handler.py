import re
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import Field
from app.common.crud_handler import CrudHandler
from app.common.responses import (
    NotFoundException,
    InternalServerErrorException,
    ListResponse,
    IdResponse,
)
from app.common.types import PkBaseModel
from app.common.db import DbCollection


class DummyModel(PkBaseModel):
    a: int = Field(...)
    b: str = Field(...)


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.db = MagicMock()
    req.app.state.logger = MagicMock()
    return req


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user123"
    return user


@pytest.fixture
def handler(mock_request, mock_user):
    instance = CrudHandler(
        mock_request, mock_user, DbCollection.ACTIVITIES, "TestEntity"
    )
    mock_request.app.state.db.get_collection.assert_called_with("activities")
    return instance


@pytest.fixture
def mapper_fn():
    return MagicMock(side_effect=lambda d: {"mapped": d})


class TestGetListed:
    @pytest.mark.asyncio
    async def test_success(self, handler, mapper_fn):
        collection = handler.collection
        collection.find.return_value.to_list = AsyncMock(
            return_value=[{"a": 1}, {"a": 2}]
        )
        result = await handler.get_listed(mapper_fn)
        collection.find.assert_called_once_with({"user_id": handler.user.id})
        assert isinstance(result, ListResponse)
        assert mapper_fn.call_count == 2
        assert result.entities == [{"mapped": {"a": 1}}, {"mapped": {"a": 2}}]

    @pytest.mark.asyncio
    async def test_empty(self, handler, mapper_fn):
        collection = handler.collection
        collection.find.return_value.to_list = AsyncMock(return_value=[])
        result = await handler.get_listed(mapper_fn)
        assert isinstance(result, ListResponse)
        assert result.entities == []
        mapper_fn.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_error(self, handler, mapper_fn):
        collection = handler.collection
        collection.find.return_value.to_list = AsyncMock(
            side_effect=Exception("db fail")
        )
        with pytest.raises(InternalServerErrorException):
            await handler.get_listed(mapper_fn)
        handler.logger.error.assert_called()


class TestGetSingle:
    @pytest.mark.asyncio
    async def test_success(self, handler, mapper_fn):
        collection = handler.collection
        collection.find_one = AsyncMock(return_value={"a": 1, "b": "foo"})
        result = await handler.get_single("id1", mapper_fn)
        collection.find_one.assert_called_once_with(
            {"user_id": handler.user.id, "id": "id1"}
        )
        mapper_fn.assert_called_once_with({"a": 1, "b": "foo"})
        handler.logger.info.assert_called_once()
        assert result == {"mapped": {"a": 1, "b": "foo"}}

    @pytest.mark.asyncio
    async def test_not_found(self, handler, mapper_fn):
        collection = handler.collection
        collection.find_one = AsyncMock(return_value=None)
        with pytest.raises(NotFoundException):
            await handler.get_single("id1", mapper_fn)

    @pytest.mark.asyncio
    async def test_db_error(self, handler, mapper_fn):
        collection = handler.collection
        collection.find_one = AsyncMock(side_effect=Exception("db fail"))
        with pytest.raises(InternalServerErrorException):
            await handler.get_single("id1", mapper_fn)
        handler.logger.error.assert_called()


class TestCreate:
    @pytest.mark.asyncio
    async def test_success(self, handler, mapper_fn):
        collection = handler.collection
        body = DummyModel(a=5, b="bar")
        collection.insert_one = AsyncMock(
            return_value=MagicMock(acknowledged=True, inserted_id="mongoid")
        )
        collection.find_one = AsyncMock(return_value={"a": 5, "b": "bar"})
        result = await handler.create(body, mapper_fn)
        collection.insert_one.assert_called()
        collection.find_one.assert_called_with({"_id": "mongoid"})
        mapper_fn.assert_called_once_with({"a": 5, "b": "bar"})
        handler.logger.info.assert_called_once()
        assert result == {"mapped": {"a": 5, "b": "bar"}}

    @pytest.mark.asyncio
    async def test_not_acknowledged(self, handler, mapper_fn):
        collection = handler.collection
        body = DummyModel(a=5, b="bar")
        collection.insert_one = AsyncMock(return_value=MagicMock(acknowledged=False))
        with pytest.raises(InternalServerErrorException):
            await handler.create(body, mapper_fn)
        handler.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_find_one_none(self, handler, mapper_fn):
        collection = handler.collection
        body = DummyModel(a=5, b="bar")
        collection.insert_one = AsyncMock(
            return_value=MagicMock(acknowledged=True, inserted_id="mongoid")
        )
        collection.find_one = AsyncMock(return_value=None)
        with pytest.raises(InternalServerErrorException):
            await handler.create(body, mapper_fn)
        handler.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_db_error(self, handler, mapper_fn):
        collection = handler.collection
        body = DummyModel(a=5, b="bar")
        collection.insert_one = AsyncMock(side_effect=Exception("db fail"))
        with pytest.raises(InternalServerErrorException):
            await handler.create(body, mapper_fn)
        handler.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_create_timestamp_true(self, handler, mapper_fn):
        collection = handler.collection
        body = DummyModel(a=7, b="baz")
        collection.insert_one = AsyncMock(
            return_value=MagicMock(acknowledged=True, inserted_id="mongoid")
        )
        collection.find_one = AsyncMock(return_value={"a": 7, "b": "baz"})
        # Patch datetime to a fixed value for testability
        with patch("app.common.crud_handler.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2025, 7, 16, 12, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.timezone = timezone
            result = await handler.create(body, mapper_fn, create_timestamp=True)
            # Check that 'created_at' was set in the inserted document
            args, kwargs = collection.insert_one.call_args
            inserted = args[0]
            assert "created_at" in inserted
            # Should be ISO format with 'Z' or '+00:00'
            assert re.match(
                r"^2025-07-16T12:00:00(\+00:00|Z)$", inserted["created_at"]
            ) or inserted["created_at"].endswith("Z")
            assert result == {"mapped": {"a": 7, "b": "baz"}}

    @pytest.mark.asyncio
    async def test_create_timestamp_false(self, handler, mapper_fn):
        collection = handler.collection
        body = DummyModel(a=8, b="qux")
        collection.insert_one = AsyncMock(
            return_value=MagicMock(acknowledged=True, inserted_id="mongoid")
        )
        collection.find_one = AsyncMock(return_value={"a": 8, "b": "qux"})
        result = await handler.create(body, mapper_fn, create_timestamp=False)
        args, kwargs = collection.insert_one.call_args
        inserted = args[0]
        assert "created_at" not in inserted
        assert result == {"mapped": {"a": 8, "b": "qux"}}


class TestUpdate:
    @pytest.mark.asyncio
    async def test_success(self, handler, mapper_fn):
        collection = handler.collection
        collection.find_one_and_update = AsyncMock(return_value={"a": 1, "b": "bar"})
        result = await handler.update("id1", DummyModel(a=1, b="bar"), mapper_fn)
        collection.find_one_and_update.assert_called()
        mapper_fn.assert_called_once_with({"a": 1, "b": "bar"})
        handler.logger.info.assert_called_once()
        assert result == {"mapped": {"a": 1, "b": "bar"}}

    @pytest.mark.asyncio
    async def test_not_found(self, handler, mapper_fn):
        collection = handler.collection
        collection.find_one_and_update = AsyncMock(return_value=None)
        with pytest.raises(NotFoundException):
            await handler.update("id1", DummyModel(a=1, b="bar"), mapper_fn)

    @pytest.mark.asyncio
    async def test_db_error(self, handler, mapper_fn):
        collection = handler.collection
        collection.find_one_and_update = AsyncMock(side_effect=Exception("db fail"))
        with pytest.raises(InternalServerErrorException):
            await handler.update("id1", DummyModel(a=1, b="bar"), mapper_fn)
        handler.logger.error.assert_called()


class TestDelete:
    @pytest.mark.asyncio
    async def test_success(self, handler):
        collection = handler.collection
        collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        result = await handler.delete("id1")
        collection.delete_one.assert_called_once_with(
            {"user_id": handler.user.id, "id": "id1"}
        )
        assert isinstance(result, IdResponse)
        assert result.id == "id1"

    @pytest.mark.asyncio
    async def test_not_found(self, handler):
        collection = handler.collection
        collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        with pytest.raises(NotFoundException):
            await handler.delete("id1")

    @pytest.mark.asyncio
    async def test_db_error(self, handler):
        collection = handler.collection
        collection.delete_one = AsyncMock(side_effect=Exception("db fail"))
        with pytest.raises(InternalServerErrorException):
            await handler.delete("id1")
        handler.logger.error.assert_called()
