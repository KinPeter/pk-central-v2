import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request

from app.common.responses import InternalServerErrorException
from app.modules.trips.get_trips import get_trips


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def logger():
    return MagicMock()


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def flights_collection():
    return MagicMock()


@pytest.fixture
def visits_collection():
    return MagicMock()


@pytest.fixture
def req(db, logger):
    req = MagicMock(spec=Request)
    req.app.state.db = db
    req.app.state.logger = logger
    return req


def setup_collections(db, flights_collection, visits_collection):
    def get_collection(name):
        return flights_collection if name == "flights" else visits_collection
    db.get_collection.side_effect = get_collection


# ── get_trips ─────────────────────────────────────────────────────────────────

class TestGetTrips:
    @pytest.mark.asyncio
    async def test_no_filter_queries_all_flights_and_visits(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        monkeypatch.setattr("app.modules.trips.get_trips.to_flight", lambda x: x)
        monkeypatch.setattr("app.modules.trips.get_trips.to_visit", lambda x: x)

        await get_trips(req, "user1")

        flights_collection.find.assert_called_once_with({"user_id": "user1"})
        visits_collection.find.assert_called_once_with({"user_id": "user1"})

    @pytest.mark.asyncio
    async def test_year_filter_applies_date_regex_to_flights(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        monkeypatch.setattr("app.modules.trips.get_trips.to_flight", lambda x: x)
        monkeypatch.setattr("app.modules.trips.get_trips.to_visit", lambda x: x)

        await get_trips(req, "user1", year=["2024"])

        flights_collection.find.assert_called_once_with(
            {"user_id": "user1", "date": {"$regex": "^(2024)"}}
        )

    @pytest.mark.asyncio
    async def test_year_filter_applies_year_in_to_visits(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        monkeypatch.setattr("app.modules.trips.get_trips.to_flight", lambda x: x)
        monkeypatch.setattr("app.modules.trips.get_trips.to_visit", lambda x: x)

        await get_trips(req, "user1", year=["2024"])

        visits_collection.find.assert_called_once_with(
            {"user_id": "user1", "year": {"$in": ["2024"]}}
        )

    @pytest.mark.asyncio
    async def test_multi_year_filter_builds_combined_regex(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        monkeypatch.setattr("app.modules.trips.get_trips.to_flight", lambda x: x)
        monkeypatch.setattr("app.modules.trips.get_trips.to_visit", lambda x: x)

        await get_trips(req, "user1", year=["2024", "2023"])

        flights_collection.find.assert_called_once_with(
            {"user_id": "user1", "date": {"$regex": "^(2024|2023)"}}
        )
        visits_collection.find.assert_called_once_with(
            {"user_id": "user1", "year": {"$in": ["2024", "2023"]}}
        )

    @pytest.mark.asyncio
    async def test_explicit_none_year_does_not_filter(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        monkeypatch.setattr("app.modules.trips.get_trips.to_flight", lambda x: x)
        monkeypatch.setattr("app.modules.trips.get_trips.to_visit", lambda x: x)

        await get_trips(req, "user1", year=None)

        flights_collection.find.assert_called_once_with({"user_id": "user1"})
        visits_collection.find.assert_called_once_with({"user_id": "user1"})

    @pytest.mark.asyncio
    async def test_returns_converted_flights_and_visits(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        raw_flight = {"_id": "f1", "user_id": "user1"}
        raw_visit = {"_id": "v1", "user_id": "user1"}
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[raw_flight])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[raw_visit])
        converted_flight = MagicMock()
        converted_visit = MagicMock()
        monkeypatch.setattr("app.modules.trips.get_trips.to_flight", lambda x: converted_flight)
        monkeypatch.setattr("app.modules.trips.get_trips.to_visit", lambda x: converted_visit)
        fake_trips = MagicMock()
        mock_trips_cls = MagicMock(return_value=fake_trips)
        monkeypatch.setattr("app.modules.trips.get_trips.Trips", mock_trips_cls)

        result = await get_trips(req, "user1")

        mock_trips_cls.assert_called_once_with(
            flights=[converted_flight],
            visits=[converted_visit],
        )
        assert result is fake_trips

    @pytest.mark.asyncio
    async def test_db_error_raises_internal_server_error(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(
            side_effect=Exception("db boom")
        )

        with pytest.raises(InternalServerErrorException):
            await get_trips(req, "user1")
