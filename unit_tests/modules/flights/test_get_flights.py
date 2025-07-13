import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from app.modules.flights.get_flights import get_flights
from app.common.responses import InternalServerErrorException, ListResponse
from app.modules.flights.flights_types import Flight


@pytest.fixture
def user():
    u = MagicMock()
    u.id = "user123"
    return u


@pytest.fixture
def logger():
    return MagicMock()


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def collection():
    return MagicMock()


@pytest.fixture
def req(db, logger):
    req = MagicMock(spec=Request)
    req.app.state.db = db
    req.app.state.logger = logger
    return req


@pytest.mark.asyncio
async def test_get_flights_success(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    item = {"id": "f1", "user_id": "user123"}
    collection.find.return_value.to_list = AsyncMock(return_value=[item])
    monkeypatch.setattr("app.modules.flights.get_flights.to_flight", lambda x: x)

    result = await get_flights(req, user)
    assert isinstance(result, ListResponse)
    assert result.entities == [item]
    db.get_collection.assert_called_once_with("flights")
    collection.find.assert_called_once_with({"user_id": "user123"})
    collection.find.return_value.to_list.assert_awaited_once_with(length=None)


@pytest.mark.asyncio
async def test_get_flights_with_is_planned(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    item = {"id": "f2", "user_id": "user123", "is_planned": True}
    collection.find.return_value.to_list = AsyncMock(return_value=[item])
    monkeypatch.setattr("app.modules.flights.get_flights.to_flight", lambda x: x)

    result = await get_flights(req, user, is_planned=True)
    collection.find.assert_called_once_with({"user_id": "user123", "is_planned": True})
    assert result.entities == [item]


@pytest.mark.asyncio
async def test_get_flights_empty(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[])
    monkeypatch.setattr("app.modules.flights.get_flights.to_flight", lambda x: x)

    result = await get_flights(req, user)
    assert isinstance(result, ListResponse)
    assert result.entities == []


@pytest.mark.asyncio
async def test_get_flights_db_error(monkeypatch, user, req, db, logger):
    db.get_collection.side_effect = Exception("db error")

    with pytest.raises(InternalServerErrorException) as exc_info:
        await get_flights(req, user)
    assert "db error" in str(exc_info.value)
    logger.error.assert_called()
