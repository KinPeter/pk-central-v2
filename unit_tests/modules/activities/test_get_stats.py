import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from app.common.responses import NotFoundException, InternalServerErrorException
from app.modules.activities.get_stats import get_stats
from app.modules.activities.activities_types import ActivitiesStats


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.db = MagicMock()
    req.app.state.logger = MagicMock()
    req.app.state.env = MagicMock()
    return req


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user123"
    return user


def _make_cursor(docs: list[dict]) -> AsyncMock:
    """Create an async cursor mock that returns the given docs via to_list."""
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=docs)
    return cursor


class TestGetStats:
    CONFIG_DATA = {
        "id": "cfg1",
        "chores": [
            {"id": "chore1", "name": "Chain", "km_interval": 500, "last_km": 1234.5}
        ],
        "walk_weekly_goal": 20,
        "walk_monthly_goal": 80,
        "cycling_weekly_goal": 50,
        "cycling_monthly_goal": 200,
        "steps_weekly_goal": 35000,
        "steps_monthly_goal": 140000,
    }

    SYNC_META_DATA = {
        "user_id": "user123",
        "synced_ids": ["strava_1", "strava_2"],
        "current_bike_kms": 250.5,
        "last_synced": "2026-06-08T12:00:00+00:00",
    }

    @pytest.mark.asyncio
    async def test_get_stats_success(self, mock_request, mock_user):
        """All collections return data — stats computed correctly."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        config_collection = mock_request.app.state.db.get_collection.return_value
        config_collection.find_one = AsyncMock(return_value=self.CONFIG_DATA)

        # Simulate sync_meta lookup — first call returns sync meta
        # We need to control which collection returns what, so we use side_effect
        # based on collection name. But the mock setup below is simpler.

        # Let's set up the mock so each get_collection returns an appropriate mock
        mock_collections = {}

        def get_collection_side_effect(name):
            if name not in mock_collections:
                coll = MagicMock()
                coll.find_one = AsyncMock()
                coll.find = MagicMock()
                mock_collections[name] = coll
            return mock_collections[name]

        mock_request.app.state.db.get_collection.side_effect = (
            get_collection_side_effect
        )

        # Config collection
        config_coll = mock_request.app.state.db.get_collection("activities_config")
        config_coll.find_one = AsyncMock(return_value=self.CONFIG_DATA)

        # Sync meta collection
        sync_coll = mock_request.app.state.db.get_collection("activities_sync_meta")
        sync_coll.find_one = AsyncMock(return_value=self.SYNC_META_DATA)

        # Activities collection — return different docs based on query
        def find_side_effect(filter):
            if filter.get("type") == "walk":
                return _make_cursor(
                    [
                        {"distance": 5000.0},  # 5.0 km
                        {"distance": 3000.0},  # 3.0 km
                    ]
                )
            elif filter.get("type") == "ride":
                return _make_cursor(
                    [
                        {"distance": 15000.0},  # 15.0 km
                    ]
                )
            return _make_cursor([])

        act_coll = mock_request.app.state.db.get_collection("activities")
        act_coll.find = MagicMock(side_effect=find_side_effect)

        # Steps collection
        steps_coll = mock_request.app.state.db.get_collection("steps")
        steps_coll.find = MagicMock(
            return_value=_make_cursor(
                [
                    {"steps": 8000, "date": today},
                    {"steps": 5000, "date": today},
                ]
            )
        )

        result = await get_stats(mock_request, mock_user)

        assert isinstance(result, ActivitiesStats)
        assert result.id == "cfg1"
        assert len(result.chores) == 1
        assert result.chores[0].name == "Chain"
        assert result.chores[0].km_interval == 500
        assert result.walk_weekly_goal == 20
        assert result.walk_monthly_goal == 80
        assert result.cycling_weekly_goal == 50
        assert result.cycling_monthly_goal == 200
        assert result.steps_weekly_goal == 35000
        assert result.steps_monthly_goal == 140000

        # Walk: (5000 + 3000) / 1000 = 8.0 km
        assert result.walk.this_week == 8.0
        assert result.walk.this_month == 8.0

        # Cycling: 15000 / 1000 = 15.0 km
        assert result.cycling.this_week == 15.0

        # Steps: 8000 + 5000 = 13000
        assert result.steps.this_week == 13000.0
        assert result.steps.this_month == 13000.0

        # current_bike_kms from sync meta
        assert result.current_bike_kms == 250.5

    @pytest.mark.asyncio
    async def test_get_stats_config_not_found(self, mock_request, mock_user):
        """Config not found raises NotFoundException."""
        mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
            return_value=None
        )

        with pytest.raises(NotFoundException):
            await get_stats(mock_request, mock_user)

        mock_request.app.state.logger.error.assert_called_with(
            f"Activities config not found for user {mock_user.id}"
        )

    @pytest.mark.asyncio
    async def test_get_stats_internal_error(self, mock_request, mock_user):
        """Unexpected error raises InternalServerErrorException."""
        mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
            side_effect=Exception("db error")
        )

        with pytest.raises(InternalServerErrorException):
            await get_stats(mock_request, mock_user)

        mock_request.app.state.logger.error.assert_any_call(
            f"Error computing activities stats for user {mock_user.id}: db error"
        )

    @pytest.mark.asyncio
    async def test_get_stats_sync_meta_not_found(self, mock_request, mock_user):
        """Missing sync meta raises NotFoundException."""
        mock_collections = {}

        def get_collection_side_effect(name):
            if name not in mock_collections:
                coll = MagicMock()
                coll.find_one = AsyncMock()
                coll.find = MagicMock()
                mock_collections[name] = coll
            return mock_collections[name]

        mock_request.app.state.db.get_collection.side_effect = (
            get_collection_side_effect
        )

        # Config exists
        config_coll = mock_request.app.state.db.get_collection("activities_config")
        config_coll.find_one = AsyncMock(return_value=self.CONFIG_DATA)

        # Sync meta does not exist
        sync_coll = mock_request.app.state.db.get_collection("activities_sync_meta")
        sync_coll.find_one = AsyncMock(return_value=None)

        with pytest.raises(NotFoundException):
            await get_stats(mock_request, mock_user)

        mock_request.app.state.logger.error.assert_called_with(
            f"Activities sync meta not found for user {mock_user.id}"
        )
