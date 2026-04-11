import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request

from app.common.responses import InternalServerErrorException
from app.modules.trips.get_trips_maps import get_trips_maps
from app.modules.trips.get_trips_stats import get_trips_stats
from app.modules.trips.trips_types import TripsMapsRequest, TripsStatsRequest


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


def _patch_stats(monkeypatch, flights_collection, visits_collection):
    """Patch all compute functions and response model for stats handler tests."""
    monkeypatch.setattr("app.modules.trips.get_trips_stats.to_flight", lambda x: x)
    monkeypatch.setattr("app.modules.trips.get_trips_stats.to_visit", lambda x: x)
    monkeypatch.setattr("app.modules.trips.get_trips_stats.compute_flights_stats", lambda f, years_filter=None: MagicMock())
    monkeypatch.setattr("app.modules.trips.get_trips_stats.compute_visits_stats", lambda v: MagicMock())
    monkeypatch.setattr("app.modules.trips.get_trips_stats.TripsStats", MagicMock(return_value=MagicMock()))


def _patch_maps(monkeypatch, flights_collection, visits_collection):
    """Patch all compute functions and response model for maps handler tests."""
    monkeypatch.setattr("app.modules.trips.get_trips_maps.to_flight", lambda x: x)
    monkeypatch.setattr("app.modules.trips.get_trips_maps.to_visit", lambda x: x)
    monkeypatch.setattr("app.modules.trips.get_trips_maps.compute_flights_map", lambda f: MagicMock())
    monkeypatch.setattr("app.modules.trips.get_trips_maps.compute_visits_map", lambda v: MagicMock())
    monkeypatch.setattr("app.modules.trips.get_trips_maps.TripsMaps", MagicMock(return_value=MagicMock()))


# ── get_trips_stats ───────────────────────────────────────────────────────────

class TestGetTripsStats:
    @pytest.mark.asyncio
    async def test_no_filters_fetches_all_completed_flights_and_all_visits(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_stats(monkeypatch, flights_collection, visits_collection)

        await get_trips_stats(req, "user1", TripsStatsRequest())

        flights_collection.find.assert_called_once_with({"user_id": "user1", "is_planned": False})
        visits_collection.find.assert_called_once_with({"user_id": "user1"})

    @pytest.mark.asyncio
    async def test_year_filter_uses_regex_for_flights_and_in_for_visits(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_stats(monkeypatch, flights_collection, visits_collection)

        await get_trips_stats(req, "user1", TripsStatsRequest(year=["2024"]))

        flights_collection.find.assert_called_once_with({
            "user_id": "user1", "is_planned": False, "date": {"$regex": "^(2024)"}
        })
        visits_collection.find.assert_called_once_with({
            "user_id": "user1", "year": {"$in": ["2024"]}
        })

    @pytest.mark.asyncio
    async def test_year_filter_with_multiple_years(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_stats(monkeypatch, flights_collection, visits_collection)

        await get_trips_stats(req, "user1", TripsStatsRequest(year=["2022", "2023"]))

        flights_collection.find.assert_called_once_with({
            "user_id": "user1", "is_planned": False, "date": {"$regex": "^(2022|2023)"}
        })
        visits_collection.find.assert_called_once_with({
            "user_id": "user1", "year": {"$in": ["2022", "2023"]}
        })

    @pytest.mark.asyncio
    async def test_flight_ids_filter_applied_when_no_year(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_stats(monkeypatch, flights_collection, visits_collection)

        await get_trips_stats(req, "user1", TripsStatsRequest(flight_ids=["f1", "f2"]))

        flights_collection.find.assert_called_once_with({
            "user_id": "user1", "is_planned": False, "id": {"$in": ["f1", "f2"]}
        })

    @pytest.mark.asyncio
    async def test_visit_ids_filter_applied_when_no_year(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_stats(monkeypatch, flights_collection, visits_collection)

        await get_trips_stats(req, "user1", TripsStatsRequest(visit_ids=["v1"]))

        visits_collection.find.assert_called_once_with({
            "user_id": "user1", "id": {"$in": ["v1"]}
        })

    @pytest.mark.asyncio
    async def test_year_takes_priority_over_flight_ids(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_stats(monkeypatch, flights_collection, visits_collection)

        await get_trips_stats(req, "user1", TripsStatsRequest(year=["2024"], flight_ids=["f1"]))

        call_args = flights_collection.find.call_args[0][0]
        assert "id" not in call_args
        assert "date" in call_args

    @pytest.mark.asyncio
    async def test_year_passes_filter_to_compute_flights_stats(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        monkeypatch.setattr("app.modules.trips.get_trips_stats.to_flight", lambda x: x)
        monkeypatch.setattr("app.modules.trips.get_trips_stats.to_visit", lambda x: x)
        monkeypatch.setattr("app.modules.trips.get_trips_stats.compute_visits_stats", lambda v: MagicMock())
        monkeypatch.setattr("app.modules.trips.get_trips_stats.TripsStats", MagicMock(return_value=MagicMock()))
        captured = {}
        def mock_compute(flights, years_filter=None):
            captured["years_filter"] = years_filter
            return MagicMock()
        monkeypatch.setattr("app.modules.trips.get_trips_stats.compute_flights_stats", mock_compute)

        await get_trips_stats(req, "user1", TripsStatsRequest(year=["2023"]))

        assert captured["years_filter"] == ["2023"]

    @pytest.mark.asyncio
    async def test_db_error_raises_internal_server_error(
        self, req, db, logger
    ):
        db.get_collection.side_effect = Exception("db boom")

        with pytest.raises(InternalServerErrorException):
            await get_trips_stats(req, "user1", TripsStatsRequest())
        logger.error.assert_called_once()


# ── get_trips_maps ────────────────────────────────────────────────────────────

class TestGetTripsMaps:
    @pytest.mark.asyncio
    async def test_no_filters_fetches_all_completed_flights_and_all_visits(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_maps(monkeypatch, flights_collection, visits_collection)

        await get_trips_maps(req, "user1", TripsMapsRequest())

        flights_collection.find.assert_called_once_with({"user_id": "user1", "is_planned": False})
        visits_collection.find.assert_called_once_with({"user_id": "user1"})

    @pytest.mark.asyncio
    async def test_year_filter_uses_regex_for_flights_and_in_for_visits(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_maps(monkeypatch, flights_collection, visits_collection)

        await get_trips_maps(req, "user1", TripsMapsRequest(year=["2024"]))

        flights_collection.find.assert_called_once_with({
            "user_id": "user1", "is_planned": False, "date": {"$regex": "^(2024)"}
        })
        visits_collection.find.assert_called_once_with({
            "user_id": "user1", "year": {"$in": ["2024"]}
        })

    @pytest.mark.asyncio
    async def test_flight_ids_filter_applied_when_no_year(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_maps(monkeypatch, flights_collection, visits_collection)

        await get_trips_maps(req, "user1", TripsMapsRequest(flight_ids=["f1"]))

        flights_collection.find.assert_called_once_with({
            "user_id": "user1", "is_planned": False, "id": {"$in": ["f1"]}
        })

    @pytest.mark.asyncio
    async def test_visit_ids_filter_applied_when_no_year(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_maps(monkeypatch, flights_collection, visits_collection)

        await get_trips_maps(req, "user1", TripsMapsRequest(visit_ids=["v1", "v2"]))

        visits_collection.find.assert_called_once_with({
            "user_id": "user1", "id": {"$in": ["v1", "v2"]}
        })

    @pytest.mark.asyncio
    async def test_year_takes_priority_over_flight_ids(
        self, monkeypatch, req, db, flights_collection, visits_collection
    ):
        setup_collections(db, flights_collection, visits_collection)
        flights_collection.find.return_value.to_list = AsyncMock(return_value=[])
        visits_collection.find.return_value.to_list = AsyncMock(return_value=[])
        _patch_maps(monkeypatch, flights_collection, visits_collection)

        await get_trips_maps(req, "user1", TripsMapsRequest(year=["2024"], flight_ids=["f1"]))

        call_args = flights_collection.find.call_args[0][0]
        assert "id" not in call_args
        assert "date" in call_args

    @pytest.mark.asyncio
    async def test_db_error_raises_internal_server_error(
        self, req, db, logger
    ):
        db.get_collection.side_effect = Exception("db boom")

        with pytest.raises(InternalServerErrorException):
            await get_trips_maps(req, "user1", TripsMapsRequest())
        logger.error.assert_called_once()
