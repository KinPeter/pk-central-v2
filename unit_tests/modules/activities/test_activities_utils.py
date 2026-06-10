import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.activities.activities_utils import (
    create_initial_activities_config,
    sum_distance,
    sum_steps,
    to_activity,
)
from app.modules.activities.activities_types import ActivityType


class TestCreateInitialActivitiesConfig:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        collection = AsyncMock()
        db.get_collection.return_value = collection
        return db, collection

    @pytest.fixture
    def mock_logger(self):
        return MagicMock()

    @pytest.fixture
    def user_id(self):
        return "user123"

    @pytest.mark.asyncio
    async def test_create_initial_activities_config_success(
        self, mock_db, mock_logger, user_id
    ):
        db, collection = mock_db
        collection.find_one.return_value = None
        logger = mock_logger

        await create_initial_activities_config(db, logger, user_id)

        db.get_collection.assert_any_call("activities_config")
        collection.find_one.assert_awaited_with({"user_id": user_id})
        assert collection.insert_one.await_count == 1
        logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_create_initial_activities_config_already_exists(
        self, mock_db, mock_logger, user_id
    ):
        db, collection = mock_db
        collection.find_one.return_value = {"user_id": user_id}
        logger = mock_logger

        with pytest.raises(ValueError):
            await create_initial_activities_config(db, logger, user_id)

        db.get_collection.assert_any_call("activities_config")
        collection.find_one.assert_awaited_with({"user_id": user_id})
        logger.warning.assert_called()
        collection.insert_one.assert_not_awaited()


class TestSumDistance:
    """Tests for sum_distance utility function."""

    @pytest.fixture
    def mock_coll_with_cursor(self):
        coll = MagicMock()
        cursor = AsyncMock()
        cursor.to_list = AsyncMock()
        coll.find = MagicMock(return_value=cursor)
        return coll, cursor

    @pytest.mark.asyncio
    async def test_sum_distance_happy_path(self, mock_coll_with_cursor):
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = [
            {"distance": 5000.0},
            {"distance": 3000.0},
            {"distance": 2000.0},
        ]

        result = await sum_distance(coll, "user1", "walk", "2026-01-01", "2026-01-07")

        assert result == 10.0  # (5000 + 3000 + 2000) / 1000 = 10.0
        coll.find.assert_called_once()
        call_filter = coll.find.call_args[0][0]
        assert call_filter["user_id"] == "user1"
        assert call_filter["type"] == "walk"

    @pytest.mark.asyncio
    async def test_sum_distance_empty(self, mock_coll_with_cursor):
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = []

        result = await sum_distance(coll, "user1", "ride", "2026-01-01", "2026-01-07")

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_sum_distance_missing_distance_field(self, mock_coll_with_cursor):
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = [
            {"distance": 5000.0},
            {"name": "no distance"},  # missing distance key
            {"distance": 3000.0},
        ]

        result = await sum_distance(coll, "user1", "walk", "2026-01-01", "2026-01-07")

        assert result == 8.0  # (5000 + 0 + 3000) / 1000 = 8.0

    @pytest.mark.asyncio
    async def test_sum_distance_single_doc(self, mock_coll_with_cursor):
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = [{"distance": 7500.0}]

        result = await sum_distance(coll, "user1", "ride", "2026-06-01", "2026-06-30")

        assert result == 7.5

    @pytest.mark.asyncio
    async def test_sum_distance_rounding(self, mock_coll_with_cursor):
        """Verify rounding to 1 decimal place."""
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = [{"distance": 1234.0}]

        result = await sum_distance(coll, "user1", "walk", "2026-01-01", "2026-01-07")

        assert result == 1.2  # 1234 / 1000 = 1.234 -> round to 1.2

    @pytest.mark.asyncio
    async def test_sum_distance_same_type_different_users(self, mock_coll_with_cursor):
        """Ensure the filter includes the correct user_id."""
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = [{"distance": 10000.0}]

        await sum_distance(coll, "user456", "walk", "2026-01-01", "2026-01-07")

        call_filter = coll.find.call_args[0][0]
        assert call_filter["user_id"] == "user456"


class TestSumSteps:
    """Tests for sum_steps utility function."""

    @pytest.fixture
    def mock_coll_with_cursor(self):
        coll = MagicMock()
        cursor = AsyncMock()
        cursor.to_list = AsyncMock()
        coll.find = MagicMock(return_value=cursor)
        return coll, cursor

    @pytest.mark.asyncio
    async def test_sum_steps_happy_path(self, mock_coll_with_cursor):
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = [
            {"steps": 8000, "date": "2026-06-01"},
            {"steps": 5000, "date": "2026-06-02"},
            {"steps": 7000, "date": "2026-06-03"},
        ]

        result = await sum_steps(coll, "user1", "2026-06-01", "2026-06-07")

        assert result == 20000.0
        coll.find.assert_called_once()
        call_filter = coll.find.call_args[0][0]
        assert call_filter["user_id"] == "user1"
        assert call_filter["date"]["$gte"] == "2026-06-01"
        assert call_filter["date"]["$lte"] == "2026-06-07"

    @pytest.mark.asyncio
    async def test_sum_steps_empty(self, mock_coll_with_cursor):
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = []

        result = await sum_steps(coll, "user1", "2026-01-01", "2026-01-31")

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_sum_steps_missing_steps_field(self, mock_coll_with_cursor):
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = [
            {"steps": 10000},
            {"date": "2026-06-02"},  # missing steps key
            {"steps": 5000},
        ]

        result = await sum_steps(coll, "user1", "2026-06-01", "2026-06-07")

        assert result == 15000.0  # 10000 + 0 + 5000

    @pytest.mark.asyncio
    async def test_sum_steps_zero_steps(self, mock_coll_with_cursor):
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = [
            {"steps": 0, "date": "2026-06-01"},
            {"steps": 0, "date": "2026-06-02"},
        ]

        result = await sum_steps(coll, "user1", "2026-06-01", "2026-06-07")

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_sum_steps_float_conversion(self, mock_coll_with_cursor):
        """Verify the result is a float even with int inputs."""
        coll, cursor = mock_coll_with_cursor
        cursor.to_list.return_value = [
            {"steps": 8000},
        ]

        result = await sum_steps(coll, "user1", "2026-06-01", "2026-06-07")

        assert isinstance(result, float)
        assert result == 8000.0


class TestToActivity:
    """Tests for the to_activity mapper function."""

    def test_full_activity_doc(self):
        """All fields present — maps correctly."""
        doc = {
            "id": "act_123",
            "type": "ride",
            "source_id": "strava_001",
            "name": "Morning Ride",
            "start_date": "2024-06-01T12:00:00+00:00",
            "moving_time": 3600,
            "elapsed_time": 3900,
            "distance": 25000.0,
            "total_elevation_gain": 200.0,
            "average_speed": 6.94,
            "max_speed": 15.0,
            "average_heartrate": 145,
            "max_heartrate": 175,
            "average_cadence": 90,
            "max_cadence": 110,
        }
        activity = to_activity(doc)

        assert activity.id == "act_123"
        assert activity.type == ActivityType.RIDE
        assert activity.source_id == "strava_001"
        assert activity.name == "Morning Ride"
        assert activity.start_date == "2024-06-01T12:00:00+00:00"
        assert activity.moving_time == 3600
        assert activity.elapsed_time == 3900
        assert activity.distance == 25000.0
        assert activity.total_elevation_gain == 200.0
        assert activity.average_speed == 6.94
        assert activity.max_speed == 15.0
        assert activity.average_heartrate == 145
        assert activity.max_heartrate == 175
        assert activity.average_cadence == 90
        assert activity.max_cadence == 110

    def test_missing_optional_fields(self):
        """Optional fields missing — maps to None."""
        doc = {
            "id": "act_456",
            "type": "walk",
            "source_id": "strava_002",
            "name": "Evening Walk",
            "start_date": "2024-06-02T18:00:00+00:00",
            "moving_time": 1800,
            "elapsed_time": 2000,
            "distance": 3000.0,
            "total_elevation_gain": 30.0,
            "average_speed": 1.67,
            "max_speed": 2.5,
        }
        activity = to_activity(doc)

        assert activity.id == "act_456"
        assert activity.type == ActivityType.WALK
        assert activity.average_heartrate is None
        assert activity.max_heartrate is None
        assert activity.average_cadence is None
        assert activity.max_cadence is None

    def test_boating_type(self):
        """Boating type maps correctly."""
        doc = {
            "id": "act_789",
            "type": "boating",
            "source_id": "strava_003",
            "name": "Lake Trip",
            "start_date": "2024-06-03T10:00:00+00:00",
            "moving_time": 7200,
            "elapsed_time": 8000,
            "distance": 12000.0,
            "total_elevation_gain": 10.0,
            "average_speed": 1.67,
            "max_speed": 3.0,
        }
        activity = to_activity(doc)

        assert activity.id == "act_789"
        assert activity.type == ActivityType.BOATING
        assert activity.name == "Lake Trip"
