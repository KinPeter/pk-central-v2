import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from app.modules.visits.query_visits import query_visits
from app.modules.visits.visits_types import VisitQuery
from app.common.responses import InternalServerErrorException, ListResponse


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
async def test_query_visits_no_filters(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    item = {"id": "v1", "user_id": "user123", "city": "Paris", "country": "France", "lat": 48.8566, "lng": 2.3522, "year": "2022"}
    collection.find.return_value.to_list = AsyncMock(return_value=[item])
    monkeypatch.setattr("app.modules.visits.query_visits.to_visit", lambda x: x)

    result = await query_visits(req, user, VisitQuery())

    assert isinstance(result, ListResponse)
    assert result.entities == [item]
    collection.find.assert_called_once_with({"user_id": "user123"})


@pytest.mark.asyncio
async def test_query_visits_by_year(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    item = {"id": "v1", "user_id": "user123", "year": "2022"}
    collection.find.return_value.to_list = AsyncMock(return_value=[item])
    monkeypatch.setattr("app.modules.visits.query_visits.to_visit", lambda x: x)

    result = await query_visits(req, user, VisitQuery(year=["2022"]))

    assert result.entities == [item]
    collection.find.assert_called_once_with({"user_id": "user123", "year": {"$in": ["2022"]}})


@pytest.mark.asyncio
async def test_query_visits_by_multiple_years(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    items = [
        {"id": "v1", "user_id": "user123", "year": "2022"},
        {"id": "v2", "user_id": "user123", "year": "2023"},
    ]
    collection.find.return_value.to_list = AsyncMock(return_value=items)
    monkeypatch.setattr("app.modules.visits.query_visits.to_visit", lambda x: x)

    result = await query_visits(req, user, VisitQuery(year=["2022", "2023"]))

    assert len(result.entities) == 2
    collection.find.assert_called_once_with({"user_id": "user123", "year": {"$in": ["2022", "2023"]}})


@pytest.mark.asyncio
async def test_query_visits_by_country(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    item = {"id": "v1", "user_id": "user123", "country": "France"}
    collection.find.return_value.to_list = AsyncMock(return_value=[item])
    monkeypatch.setattr("app.modules.visits.query_visits.to_visit", lambda x: x)

    result = await query_visits(req, user, VisitQuery(country=["France"]))

    assert result.entities == [item]
    collection.find.assert_called_once_with({"user_id": "user123", "country": {"$in": ["France"]}})


@pytest.mark.asyncio
async def test_query_visits_by_year_and_country(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    item = {"id": "v1", "user_id": "user123", "year": "2023", "country": "France"}
    collection.find.return_value.to_list = AsyncMock(return_value=[item])
    monkeypatch.setattr("app.modules.visits.query_visits.to_visit", lambda x: x)

    result = await query_visits(req, user, VisitQuery(year=["2023"], country=["France"]))

    assert result.entities == [item]
    collection.find.assert_called_once_with({
        "user_id": "user123",
        "year": {"$in": ["2023"]},
        "country": {"$in": ["France"]},
    })


@pytest.mark.asyncio
async def test_query_visits_empty_result(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[])
    monkeypatch.setattr("app.modules.visits.query_visits.to_visit", lambda x: x)

    result = await query_visits(req, user, VisitQuery(year=["1999"]))

    assert isinstance(result, ListResponse)
    assert result.entities == []


@pytest.mark.asyncio
async def test_query_visits_db_error(user, req, db, logger):
    db.get_collection.side_effect = Exception("db error")

    with pytest.raises(InternalServerErrorException) as exc_info:
        await query_visits(req, user, VisitQuery())

    assert "db error" in str(exc_info.value)
    logger.error.assert_called()
