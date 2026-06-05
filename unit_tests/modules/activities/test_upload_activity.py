import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.activities.upload_activity import upload_activity
from app.common.responses import (
    ConflictException,
    IdResponse,
    InternalServerErrorException,
    UnprocessableEntityException,
)
from app.modules.activities.activities_types import ActivityData, ActivityType

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
def mock_gpx_file():
    """Return a mock UploadFile with valid GPX content."""
    file = MagicMock()
    file.filename = "test_activity.gpx"
    file.read = AsyncMock(
        return_value=b'<?xml version="1.0" encoding="UTF-8"?><gpx></gpx>'
    )
    return file


@pytest.fixture
def mock_walk_activity():
    """Return a sample ActivityData for a walk."""
    return ActivityData(
        type=ActivityType.WALK,
        source_id="strava_123",
        name="Morning Walk",
        start_date="2024-06-01T12:00:00+00:00",
        moving_time=1200,
        elapsed_time=1300,
        distance=2000.0,
        total_elevation_gain=50.0,
        average_speed=1.67,
        max_speed=2.5,
        average_heartrate=120,
        max_heartrate=140,
        average_cadence=80,
        max_cadence=90,
    )


@pytest.fixture
def mock_ride_activity():
    """Return a sample ActivityData for a ride (15 km)."""
    return ActivityData(
        type=ActivityType.RIDE,
        source_id="strava_456",
        name="Morning Ride",
        start_date="2024-06-01T12:00:00+00:00",
        moving_time=3600,
        elapsed_time=3900,
        distance=15000.0,
        total_elevation_gain=200.0,
        average_speed=4.17,
        max_speed=12.5,
        average_heartrate=140,
        max_heartrate=170,
        average_cadence=85,
        max_cadence=100,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_collections(mock_request, sync_meta):
    """Configure db.get_collection to return per-collection mocks.

    Args:
        mock_request: The mocked request fixture.
        sync_meta: The value for sync_meta_collection.find_one, or None.

    Returns:
        (activities_collection, sync_meta_collection) for assertions.
    """
    sync_meta_collection = MagicMock()
    sync_meta_collection.find_one = AsyncMock(return_value=sync_meta)
    sync_meta_collection.update_one = AsyncMock()
    sync_meta_collection.insert_one = AsyncMock()

    activities_collection = MagicMock()
    activities_collection.insert_one = AsyncMock()

    def _side_effect(name):
        collections = {
            "activities": activities_collection,
            "activities_sync_meta": sync_meta_collection,
        }
        return collections.get(name, MagicMock())

    mock_request.app.state.db.get_collection.side_effect = _side_effect
    return activities_collection, sync_meta_collection


# ===================================================================
# Validation tests
# ===================================================================


class TestUploadActivityValidation:
    """Tests covering input validation edge cases."""

    @pytest.mark.asyncio
    async def test_empty_source_id(self, mock_request, mock_user, mock_gpx_file):
        """Should reject a blank / whitespace-only source_id."""
        with pytest.raises(UnprocessableEntityException) as exc_info:
            await upload_activity(mock_request, mock_user, mock_gpx_file, "   ")
        assert "source_id must not be empty" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_none_gpx_file(self, mock_request, mock_user):
        """Should reject when gpx_file is None."""
        with pytest.raises(UnprocessableEntityException) as exc_info:
            await upload_activity(mock_request, mock_user, None, "strava_123")  # type: ignore[arg-type]
        assert "File must be a GPX file" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_missing_filename(self, mock_request, mock_user):
        """Should reject when gpx_file has no filename."""
        file = MagicMock()
        file.filename = None
        file.read = AsyncMock()
        with pytest.raises(UnprocessableEntityException) as exc_info:
            await upload_activity(mock_request, mock_user, file, "strava_123")
        assert "File must be a GPX file" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_wrong_extension(self, mock_request, mock_user):
        """Should reject files without a .gpx extension."""
        file = MagicMock()
        file.filename = "test.txt"
        file.read = AsyncMock()
        with pytest.raises(UnprocessableEntityException) as exc_info:
            await upload_activity(mock_request, mock_user, file, "strava_123")
        assert "File must be a GPX file" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_invalid_xml_content(self, mock_request, mock_user):
        """Should reject content that doesn't look like GPX XML."""
        file = MagicMock()
        file.filename = "test.gpx"
        file.read = AsyncMock(return_value=b"not xml content")
        with pytest.raises(UnprocessableEntityException) as exc_info:
            await upload_activity(mock_request, mock_user, file, "strava_123")
        assert "File does not appear to be a valid GPX file" in str(
            exc_info.value.detail
        )

    @pytest.mark.asyncio
    async def test_case_insensitive_extension_check(self, mock_request, mock_user):
        """Should accept .GPX (uppercase) extension."""
        file = MagicMock()
        file.filename = "ACTIVITY.GPX"
        file.read = AsyncMock(
            return_value=b'<?xml version="1.0" encoding="UTF-8"?><gpx></gpx>'
        )
        _setup_collections(mock_request, sync_meta=None)
        dummy_activity = ActivityData(
            type=ActivityType.WALK,
            source_id="strava_123",
            name="",
            start_date="2024-06-01T12:00:00+00:00",
            moving_time=0,
            elapsed_time=0,
            distance=0.0,
            total_elevation_gain=0.0,
            average_speed=0.0,
            max_speed=0.0,
            average_heartrate=None,
            max_heartrate=None,
            average_cadence=None,
            max_cadence=None,
        )
        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=dummy_activity,
        ):
            result = await upload_activity(mock_request, mock_user, file, "strava_123")
        assert isinstance(result, IdResponse)


# ===================================================================
# Happy path tests
# ===================================================================


class TestUploadActivitySuccess:
    """Tests covering the successful upload flow."""

    @pytest.mark.asyncio
    async def test_existing_user(
        self, mock_request, mock_user, mock_gpx_file, mock_walk_activity
    ):
        """Upload succeeds for an existing user with sync_meta already present."""
        source_id = "strava_123"
        sync_meta = {
            "user_id": "user123",
            "synced_ids": [],
            "current_bike_kms": 0,
            "last_synced": None,
        }
        activities_coll, sync_meta_coll = _setup_collections(mock_request, sync_meta)

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=mock_walk_activity,
        ):
            result = await upload_activity(
                mock_request, mock_user, mock_gpx_file, source_id
            )

        assert isinstance(result, IdResponse)
        assert result.id is not None
        mock_gpx_file.read.assert_called_once()

        # Activity inserted to DB
        activities_coll.insert_one.assert_called_once()
        inserted = activities_coll.insert_one.call_args[0][0]
        assert inserted["source_id"] == source_id
        assert inserted["user_id"] == "user123"
        assert inserted["type"] == "walk"
        assert "id" in inserted

        # Sync meta updated
        sync_meta_coll.update_one.assert_called_once_with(
            {"user_id": "user123"},
            {"$set": sync_meta},
        )
        assert source_id in sync_meta["synced_ids"]
        assert sync_meta["last_synced"] is not None
        assert sync_meta["current_bike_kms"] == 0  # Walk does not add kms

    @pytest.mark.asyncio
    async def test_new_user_creates_sync_meta(
        self, mock_request, mock_user, mock_gpx_file, mock_walk_activity
    ):
        """When no sync_meta exists, a new document is created before inserting."""
        source_id = "strava_123"
        activities_coll, sync_meta_coll = _setup_collections(
            mock_request, sync_meta=None
        )

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=mock_walk_activity,
        ):
            result = await upload_activity(
                mock_request, mock_user, mock_gpx_file, source_id
            )

        assert isinstance(result, IdResponse)
        assert result.id is not None

        # New sync_meta inserted (the dict is mutated in-place by the handler
        # after insert_one, so we only verify immutable fields on the insert arg)
        sync_meta_coll.insert_one.assert_called_once()
        inserted_meta = sync_meta_coll.insert_one.call_args[0][0]
        assert inserted_meta["user_id"] == "user123"
        assert isinstance(inserted_meta["synced_ids"], list)
        assert inserted_meta["current_bike_kms"] == 0

        # Then updated with the source_id appended
        sync_meta_coll.update_one.assert_called_once()
        updated_meta = sync_meta_coll.update_one.call_args[0][1]["$set"]
        assert source_id in updated_meta["synced_ids"]
        assert updated_meta["synced_ids"] == [source_id]

    @pytest.mark.asyncio
    async def test_ride_adds_bike_kms(
        self, mock_request, mock_user, mock_gpx_file, mock_ride_activity
    ):
        """A ride activity should increment current_bike_kms."""
        source_id = "strava_456"
        sync_meta = {
            "user_id": "user123",
            "synced_ids": ["strava_111"],
            "current_bike_kms": 100.0,
            "last_synced": "2024-01-01T00:00:00+00:00",
        }
        expected_kms = 100.0 + round(15000.0 / 1000, 1)  # 100 + 15.0 = 115.0
        activities_coll, sync_meta_coll = _setup_collections(mock_request, sync_meta)

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=mock_ride_activity,
        ):
            result = await upload_activity(
                mock_request, mock_user, mock_gpx_file, source_id
            )

        assert isinstance(result, IdResponse)
        assert sync_meta["current_bike_kms"] == expected_kms
        sync_meta_coll.update_one.assert_called_once_with(
            {"user_id": "user123"},
            {"$set": sync_meta},
        )

    @pytest.mark.asyncio
    async def test_boating_does_not_add_bike_kms(
        self, mock_request, mock_user, mock_gpx_file
    ):
        """A boating activity should NOT increment current_bike_kms."""
        source_id = "strava_789"
        boat_activity = ActivityData(
            type=ActivityType.BOATING,
            source_id=source_id,
            name="Lake Cruise",
            start_date="2024-06-01T12:00:00+00:00",
            moving_time=1800,
            elapsed_time=2000,
            distance=5000.0,
            total_elevation_gain=0.0,
            average_speed=2.78,
            max_speed=5.0,
            average_heartrate=None,
            max_heartrate=None,
            average_cadence=None,
            max_cadence=None,
        )
        sync_meta = {
            "user_id": "user123",
            "synced_ids": [],
            "current_bike_kms": 50.0,
            "last_synced": None,
        }
        _setup_collections(mock_request, sync_meta)

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=boat_activity,
        ):
            result = await upload_activity(
                mock_request, mock_user, mock_gpx_file, source_id
            )

        assert isinstance(result, IdResponse)
        # current_bike_kms should remain unchanged
        assert sync_meta["current_bike_kms"] == 50.0

    @pytest.mark.asyncio
    async def test_multiple_source_ids_in_sync_meta(
        self, mock_request, mock_user, mock_gpx_file, mock_walk_activity
    ):
        """New source_id is appended to existing synced_ids list."""
        source_id = "strava_999"
        sync_meta = {
            "user_id": "user123",
            "synced_ids": ["strava_111", "strava_222"],
            "current_bike_kms": 0,
            "last_synced": "2024-05-01T00:00:00+00:00",
        }
        activities_coll, sync_meta_coll = _setup_collections(mock_request, sync_meta)

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=mock_walk_activity,
        ):
            result = await upload_activity(
                mock_request, mock_user, mock_gpx_file, source_id
            )

        assert isinstance(result, IdResponse)
        assert sync_meta["synced_ids"] == ["strava_111", "strava_222", "strava_999"]
        sync_meta_coll.update_one.assert_called_once_with(
            {"user_id": "user123"},
            {"$set": sync_meta},
        )


# ===================================================================
# Error / exception tests
# ===================================================================


class TestUploadActivityErrors:
    """Tests covering error handling paths."""

    @pytest.mark.asyncio
    async def test_already_synced(
        self, mock_request, mock_user, mock_gpx_file, mock_walk_activity
    ):
        """Should raise ConflictException when source_id is already in synced_ids."""
        source_id = "strava_123"
        sync_meta = {
            "user_id": "user123",
            "synced_ids": ["strava_123", "strava_456"],
            "current_bike_kms": 50.0,
            "last_synced": "2024-01-01T00:00:00+00:00",
        }
        _setup_collections(mock_request, sync_meta)

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=mock_walk_activity,
        ):
            with pytest.raises(ConflictException) as exc_info:
                await upload_activity(mock_request, mock_user, mock_gpx_file, source_id)
        assert "Activity already synced" in str(exc_info.value.detail)

        # Should NOT have inserted an activity
        activities_coll = mock_request.app.state.db.get_collection("activities")
        activities_coll.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_strava_gpx_value_error(
        self, mock_request, mock_user, mock_gpx_file
    ):
        """ValueError from parse_strava_gpx should become UnprocessableEntity."""
        _setup_collections(mock_request, sync_meta=None)

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            side_effect=ValueError("No track points found in GPX file"),
        ):
            with pytest.raises(UnprocessableEntityException) as exc_info:
                await upload_activity(
                    mock_request, mock_user, mock_gpx_file, "strava_123"
                )
        assert "No track points found" in str(exc_info.value.detail)
        mock_request.app.state.logger.error.assert_called_with(
            "Error parsing GPX file: No track points found in GPX file"
        )

    @pytest.mark.asyncio
    async def test_insert_one_db_error(
        self, mock_request, mock_user, mock_gpx_file, mock_walk_activity
    ):
        """Generic DB exception during insert_one should become InternalServerError."""
        sync_meta = {
            "user_id": "user123",
            "synced_ids": [],
            "current_bike_kms": 0,
            "last_synced": None,
        }
        sync_meta_coll = MagicMock()
        sync_meta_coll.find_one = AsyncMock(return_value=sync_meta)
        sync_meta_coll.insert_one = AsyncMock()
        sync_meta_coll.update_one = AsyncMock()

        activities_coll = MagicMock()
        activities_coll.insert_one = AsyncMock(side_effect=Exception("db write failed"))

        def _side_effect(name):
            collections = {
                "activities": activities_coll,
                "activities_sync_meta": sync_meta_coll,
            }
            return collections.get(name, MagicMock())

        mock_request.app.state.db.get_collection.side_effect = _side_effect

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=mock_walk_activity,
        ):
            with pytest.raises(InternalServerErrorException) as exc_info:
                await upload_activity(
                    mock_request, mock_user, mock_gpx_file, "strava_123"
                )
        assert "An error occurred while uploading the activity" in str(
            exc_info.value.detail
        )
        mock_request.app.state.logger.error.assert_any_call(
            "Error uploading activity for user user123: db write failed"
        )

    @pytest.mark.asyncio
    async def test_update_one_db_error(
        self, mock_request, mock_user, mock_gpx_file, mock_walk_activity
    ):
        """Generic DB exception during update_one should become InternalServerError."""
        sync_meta = {
            "user_id": "user123",
            "synced_ids": [],
            "current_bike_kms": 0,
            "last_synced": None,
        }
        sync_meta_coll = MagicMock()
        sync_meta_coll.find_one = AsyncMock(return_value=sync_meta)
        sync_meta_coll.insert_one = AsyncMock()
        sync_meta_coll.update_one = AsyncMock(side_effect=Exception("update failed"))

        activities_coll = MagicMock()
        activities_coll.insert_one = AsyncMock()

        def _side_effect(name):
            collections = {
                "activities": activities_coll,
                "activities_sync_meta": sync_meta_coll,
            }
            return collections.get(name, MagicMock())

        mock_request.app.state.db.get_collection.side_effect = _side_effect

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=mock_walk_activity,
        ):
            with pytest.raises(InternalServerErrorException) as exc_info:
                await upload_activity(
                    mock_request, mock_user, mock_gpx_file, "strava_123"
                )
        assert "An error occurred while uploading the activity" in str(
            exc_info.value.detail
        )
        mock_request.app.state.logger.error.assert_any_call(
            "Error uploading activity for user user123: update failed"
        )

    @pytest.mark.asyncio
    async def test_find_one_db_error(
        self, mock_request, mock_user, mock_gpx_file, mock_walk_activity
    ):
        """Generic DB exception during find_one should become InternalServerError."""
        sync_meta_coll = MagicMock()
        sync_meta_coll.find_one = AsyncMock(side_effect=Exception("connection lost"))

        def _side_effect(name):
            if name == "activities_sync_meta":
                return sync_meta_coll
            return MagicMock()

        mock_request.app.state.db.get_collection.side_effect = _side_effect

        with patch(
            "app.modules.activities.upload_activity.parse_strava_gpx",
            return_value=mock_walk_activity,
        ):
            with pytest.raises(InternalServerErrorException) as exc_info:
                await upload_activity(
                    mock_request, mock_user, mock_gpx_file, "strava_123"
                )
        assert "An error occurred while uploading the activity" in str(
            exc_info.value.detail
        )
