import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.activities.query_activities import query_activities
from app.common.responses import InternalServerErrorException, ListResponse
from app.modules.activities.activities_types import (
    Activity,
    ActivityQuery,
    ActivityType,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
def sample_activity_docs():
    """Return sample MongoDB documents for activities, most recent first."""
    return [
        {
            "id": "act_3",
            "type": "ride",
            "source_id": "strava_003",
            "name": "Afternoon Ride",
            "start_date": "2024-06-03T12:00:00+00:00",
            "moving_time": 3600,
            "elapsed_time": 3900,
            "distance": 25000.0,
            "total_elevation_gain": 300.0,
            "average_speed": 6.94,
            "max_speed": 15.0,
            "average_heartrate": 145,
            "max_heartrate": 175,
            "average_cadence": 90,
            "max_cadence": 110,
        },
        {
            "id": "act_2",
            "type": "walk",
            "source_id": "strava_002",
            "name": "Morning Walk",
            "start_date": "2024-06-02T08:00:00+00:00",
            "moving_time": 1800,
            "elapsed_time": 2000,
            "distance": 3000.0,
            "total_elevation_gain": 40.0,
            "average_speed": 1.67,
            "max_speed": 2.5,
            "average_heartrate": 110,
            "max_heartrate": 130,
            "average_cadence": 75,
            "max_cadence": 85,
        },
        {
            "id": "act_1",
            "type": "boating",
            "source_id": "strava_001",
            "name": "Lake Trip",
            "start_date": "2024-06-01T10:00:00+00:00",
            "moving_time": 7200,
            "elapsed_time": 8000,
            "distance": 12000.0,
            "total_elevation_gain": 10.0,
            "average_speed": 1.67,
            "max_speed": 3.0,
            "average_heartrate": None,
            "max_heartrate": None,
            "average_cadence": None,
            "max_cadence": None,
        },
    ]


@pytest.fixture
def mock_cursor():
    """Return a mock cursor that can be chained from find().sort()."""
    cursor = MagicMock()
    cursor.to_list = AsyncMock()
    return cursor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def configure_collection(mock_request, cursor):
    """Configure db.get_collection to return a mock with the given cursor."""
    collection = MagicMock()
    collection.find.return_value.sort.return_value = cursor
    mock_request.app.state.db.get_collection.return_value = collection
    return collection


# ===================================================================
# Tests
# ===================================================================


class TestQueryActivities:
    """Tests for the query_activities handler."""

    @pytest.mark.asyncio
    async def test_no_filters_returns_all(
        self, mock_request, mock_user, sample_activity_docs, mock_cursor
    ):
        """No types and no dates — returns all activities."""
        mock_cursor.to_list.return_value = sample_activity_docs
        configure_collection(mock_request, mock_cursor)

        body = ActivityQuery()
        result = await query_activities(mock_request, body, mock_user)

        mock_request.app.state.db.get_collection.assert_called_once_with("activities")
        assert isinstance(result, ListResponse)
        assert len(result.entities) == 3

        # Verify sort order: most recent first (descending by start_date)
        assert result.entities[0].id == "act_3"
        assert result.entities[1].id == "act_2"
        assert result.entities[2].id == "act_1"

        # Verify all fields mapped correctly
        activity = result.entities[0]
        assert activity.type == ActivityType.RIDE
        assert activity.source_id == "strava_003"
        assert activity.name == "Afternoon Ride"
        assert activity.distance == 25000.0
        assert activity.average_heartrate == 145

        # Verify boating activity has None heartrate fields
        boating = result.entities[2]
        assert boating.type == ActivityType.BOATING
        assert boating.average_heartrate is None
        assert boating.max_heartrate is None
        assert boating.average_cadence is None
        assert boating.max_cadence is None

    @pytest.mark.asyncio
    async def test_filter_by_types(
        self, mock_request, mock_user, sample_activity_docs, mock_cursor
    ):
        """Filter by specific types — only matching activities returned."""
        # Return only walk and ride docs
        filtered_docs = [sample_activity_docs[0], sample_activity_docs[1]]
        mock_cursor.to_list.return_value = filtered_docs
        configure_collection(mock_request, mock_cursor)

        body = ActivityQuery(types=[ActivityType.WALK, ActivityType.RIDE])
        result = await query_activities(mock_request, body, mock_user)

        assert len(result.entities) == 2
        assert result.entities[0].type == ActivityType.RIDE
        assert result.entities[1].type == ActivityType.WALK

        # Verify $in filter was applied
        collection = mock_request.app.state.db.get_collection.return_value
        find_filter = collection.find.call_args[0][0]
        assert find_filter["user_id"] == "user123"
        assert find_filter["type"]["$in"] == ["walk", "ride"]

    @pytest.mark.asyncio
    async def test_filter_by_date_range(
        self, mock_request, mock_user, sample_activity_docs, mock_cursor
    ):
        """Filter by date range — only activities within range returned."""
        filtered_docs = [sample_activity_docs[0]]
        mock_cursor.to_list.return_value = filtered_docs
        configure_collection(mock_request, mock_cursor)

        body = ActivityQuery(from_date="2024-06-03", to_date="2024-06-03")
        result = await query_activities(mock_request, body, mock_user)

        assert len(result.entities) == 1
        assert result.entities[0].id == "act_3"

        # Verify date filter was applied
        collection = mock_request.app.state.db.get_collection.return_value
        find_filter = collection.find.call_args[0][0]
        assert find_filter["user_id"] == "user123"
        assert "$gte" in find_filter["start_date"]
        assert "$lte" in find_filter["start_date"]
        assert "T00:00:00+00:00" in find_filter["start_date"]["$gte"]
        assert "T23:59:59.999999+00:00" in find_filter["start_date"]["$lte"]

    @pytest.mark.asyncio
    async def test_filter_by_from_date_only(
        self, mock_request, mock_user, sample_activity_docs, mock_cursor
    ):
        """Filter with only from_date — $gte only in the filter."""
        mock_cursor.to_list.return_value = []
        configure_collection(mock_request, mock_cursor)

        body = ActivityQuery(from_date="2024-06-02")
        await query_activities(mock_request, body, mock_user)

        collection = mock_request.app.state.db.get_collection.return_value
        find_filter = collection.find.call_args[0][0]
        assert "$gte" in find_filter["start_date"]
        assert "$lte" not in find_filter["start_date"]

    @pytest.mark.asyncio
    async def test_filter_by_to_date_only(
        self, mock_request, mock_user, sample_activity_docs, mock_cursor
    ):
        """Filter with only to_date — $lte only in the filter."""
        mock_cursor.to_list.return_value = []
        configure_collection(mock_request, mock_cursor)

        body = ActivityQuery(to_date="2024-06-02")
        await query_activities(mock_request, body, mock_user)

        collection = mock_request.app.state.db.get_collection.return_value
        find_filter = collection.find.call_args[0][0]
        assert "$lte" in find_filter["start_date"]
        assert "$gte" not in find_filter["start_date"]

    @pytest.mark.asyncio
    async def test_combined_filters(
        self, mock_request, mock_user, sample_activity_docs, mock_cursor
    ):
        """Both types and date range — both filters applied."""
        filtered_docs = [sample_activity_docs[0]]
        mock_cursor.to_list.return_value = filtered_docs
        configure_collection(mock_request, mock_cursor)

        body = ActivityQuery(
            types=[ActivityType.RIDE],
            from_date="2024-06-01",
            to_date="2024-06-10",
        )
        result = await query_activities(mock_request, body, mock_user)

        assert len(result.entities) == 1
        assert result.entities[0].type == ActivityType.RIDE

        collection = mock_request.app.state.db.get_collection.return_value
        find_filter = collection.find.call_args[0][0]
        assert find_filter["type"]["$in"] == ["ride"]
        assert "$gte" in find_filter["start_date"]
        assert "$lte" in find_filter["start_date"]

    @pytest.mark.asyncio
    async def test_no_results(self, mock_request, mock_user, mock_cursor):
        """No matching activities — returns empty list."""
        mock_cursor.to_list.return_value = []
        configure_collection(mock_request, mock_cursor)

        body = ActivityQuery(types=[ActivityType.BOATING])
        result = await query_activities(mock_request, body, mock_user)

        assert isinstance(result, ListResponse)
        assert len(result.entities) == 0

    @pytest.mark.asyncio
    async def test_internal_error(self, mock_request, mock_user):
        """DB exception — raises InternalServerErrorException."""
        collection = MagicMock()
        collection.find.side_effect = Exception("db connection error")
        mock_request.app.state.db.get_collection.return_value = collection

        body = ActivityQuery()
        with pytest.raises(InternalServerErrorException):
            await query_activities(mock_request, body, mock_user)

        mock_request.app.state.logger.error.assert_any_call(
            "Error querying activities for user user123: db connection error"
        )
