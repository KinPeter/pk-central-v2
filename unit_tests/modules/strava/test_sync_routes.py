import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.strava.sync_routes import sync_strava_routes
from app.modules.strava.strava_types import StravaSyncResponse, StravaDbCollection


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.logger = MagicMock()
    req.app.state.env = MagicMock()
    req.app.state.env.STRAVA_DB_URI = "mongodb://strava-db-uri"
    return req


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user123"
    return user


@pytest.fixture
def mock_strava_token():
    return "dummy-token"


@pytest.mark.asyncio
@patch("app.modules.strava.sync_routes.AsyncMongoClient")
@patch("app.modules.strava.sync_routes.StravaApi")
async def test_sync_strava_routes_success(
    mock_strava_api, mock_mongo, mock_request, mock_user, mock_strava_token
):
    # Setup DB mocks
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_activities_col = MagicMock()
    mock_sync_meta_col = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)

    def get_collection_side_effect(name):
        if name == StravaDbCollection.ACTIVITIES or name == "activities":
            return mock_activities_col
        if name == StravaDbCollection.SYNC_META or name == "sync_metadata":
            return mock_sync_meta_col
        raise KeyError(name)

    mock_db.get_collection.side_effect = get_collection_side_effect
    mock_mongo.return_value = mock_client

    # Setup sync meta
    user_sync_data = {"user_id": mock_user.id, "synced_ids": [], "last_synced": None}
    mock_sync_meta_col.find_one = AsyncMock(return_value=user_sync_data)
    mock_sync_meta_col.insert_one = AsyncMock()
    mock_sync_meta_col.update_one = AsyncMock()
    mock_activities_col.insert_one = AsyncMock()
    mock_activities_col.count_documents = AsyncMock(return_value=2)

    # Setup StravaApi mocks
    mock_strava = MagicMock()
    mock_strava.get_athlete = AsyncMock(return_value={"username": "athlete1", "id": 42})
    mock_strava.get_all_activities = AsyncMock(
        return_value=[
            {
                "id": 1,
                "type": "Run",
                "start_date": datetime.now(timezone.utc).isoformat(),
                "distance": 1000,
                "name": "Morning Run",
            },
            {
                "id": 2,
                "type": "Walk",
                "start_date": datetime.now(timezone.utc).isoformat(),
                "distance": 500,
                "name": "Evening Walk",
            },
        ]
    )
    mock_strava.get_activity_latlng_stream = AsyncMock(
        return_value={"latlng": {"data": [[1, 2], [3, 4]]}}
    )
    mock_strava_api.return_value = mock_strava

    result = await sync_strava_routes(mock_request, mock_user, mock_strava_token)
    mock_client.admin.command.assert_called_once_with("ping")
    mock_client.get_database.assert_called_once_with("strava")
    mock_db.get_collection.assert_any_call(StravaDbCollection.ACTIVITIES)
    mock_db.get_collection.assert_any_call(StravaDbCollection.SYNC_META)
    mock_sync_meta_col.find_one.assert_called_once_with({"user_id": mock_user.id})
    mock_sync_meta_col.insert_one.assert_not_called()
    mock_strava_api.assert_called_once_with(
        access_token=mock_strava_token, logger=mock_request.app.state.logger
    )
    mock_strava.get_athlete.assert_called_once_with()
    mock_strava.get_all_activities.assert_called()
    mock_strava.get_activity_latlng_stream.assert_any_call(activity_id=1)
    mock_strava.get_activity_latlng_stream.assert_any_call(activity_id=2)
    assert isinstance(result, StravaSyncResponse)
    assert result.routes_synced == 2
    assert result.total_routes == 2
    assert mock_activities_col.insert_one.await_count == 2
    assert mock_sync_meta_col.update_one.await_count == 2


@pytest.mark.asyncio
@patch("app.modules.strava.sync_routes.AsyncMongoClient")
@patch("app.modules.strava.sync_routes.StravaApi")
async def test_sync_strava_routes_no_sync_meta(
    mock_strava_api, mock_mongo, mock_request, mock_user, mock_strava_token
):
    # Setup DB mocks
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_activities_col = MagicMock()
    mock_sync_meta_col = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)

    def get_collection_side_effect(name):
        if name == StravaDbCollection.ACTIVITIES or name == "activities":
            return mock_activities_col
        if name == StravaDbCollection.SYNC_META or name == "sync_metadata":
            return mock_sync_meta_col
        raise KeyError(name)

    mock_db.get_collection.side_effect = get_collection_side_effect
    mock_mongo.return_value = mock_client

    # No sync meta found
    mock_sync_meta_col.find_one = AsyncMock(return_value=None)
    mock_sync_meta_col.insert_one = AsyncMock()
    mock_sync_meta_col.update_one = AsyncMock()
    mock_activities_col.insert_one = AsyncMock()
    mock_activities_col.count_documents = AsyncMock(return_value=2)

    # Setup StravaApi mocks
    mock_strava = MagicMock()
    mock_strava.get_athlete = AsyncMock(return_value={"username": "athlete1", "id": 42})
    mock_strava.get_all_activities = AsyncMock(
        return_value=[
            {
                "id": 1,
                "type": "Run",
                "start_date": datetime.now(timezone.utc).isoformat(),
                "distance": 1000,
                "name": "Morning Run",
            },
        ]
    )
    mock_strava.get_activity_latlng_stream = AsyncMock(
        return_value={"latlng": {"data": [[1, 2], [3, 4]]}}
    )
    mock_strava_api.return_value = mock_strava

    result = await sync_strava_routes(mock_request, mock_user, mock_strava_token)
    mock_sync_meta_col.find_one.assert_called_once_with({"user_id": mock_user.id})
    mock_sync_meta_col.insert_one.assert_called_once()
    assert isinstance(result, StravaSyncResponse)
    assert result.routes_synced == 1
    assert result.total_routes == 1


@pytest.mark.asyncio
@patch("app.modules.strava.sync_routes.AsyncMongoClient")
@patch("app.modules.strava.sync_routes.StravaApi")
async def test_sync_strava_routes_empty_activities(
    mock_strava_api, mock_mongo, mock_request, mock_user, mock_strava_token
):
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_activities_col = MagicMock()
    mock_sync_meta_col = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)

    def get_collection_side_effect(name):
        if name == StravaDbCollection.ACTIVITIES or name == "activities":
            return mock_activities_col
        if name == StravaDbCollection.SYNC_META or name == "sync_metadata":
            return mock_sync_meta_col
        raise KeyError(name)

    mock_db.get_collection.side_effect = get_collection_side_effect
    mock_mongo.return_value = mock_client

    user_sync_data = {"user_id": mock_user.id, "synced_ids": [], "last_synced": None}
    mock_sync_meta_col.find_one = AsyncMock(return_value=user_sync_data)
    mock_sync_meta_col.insert_one = AsyncMock()
    mock_activities_col.count_documents = AsyncMock(return_value=0)

    mock_strava = MagicMock()
    mock_strava.get_athlete = AsyncMock(return_value={"username": "athlete1", "id": 42})
    mock_strava.get_all_activities = AsyncMock(return_value=[])
    mock_strava_api.return_value = mock_strava

    result = await sync_strava_routes(mock_request, mock_user, mock_strava_token)
    mock_client.admin.command.assert_called_once_with("ping")
    mock_client.get_database.assert_called_once_with("strava")
    mock_db.get_collection.assert_any_call(StravaDbCollection.ACTIVITIES)
    mock_db.get_collection.assert_any_call(StravaDbCollection.SYNC_META)
    mock_sync_meta_col.find_one.assert_called_once_with({"user_id": mock_user.id})
    mock_strava_api.assert_called_once_with(
        access_token=mock_strava_token, logger=mock_request.app.state.logger
    )
    mock_strava.get_athlete.assert_called_once_with()
    mock_strava.get_all_activities.assert_called_once_with()
    mock_activities_col.count_documents.assert_called_once_with(
        {"user_id": mock_user.id}
    )
    assert isinstance(result, StravaSyncResponse)
    assert result.routes_synced == 0
    assert result.total_routes == 0


@pytest.mark.asyncio
@patch("app.modules.strava.sync_routes.AsyncMongoClient")
async def test_sync_strava_routes_db_connection_error(
    mock_mongo, mock_request, mock_user, mock_strava_token
):
    mock_client = AsyncMock()
    mock_client.admin.command = AsyncMock(side_effect=Exception("db down"))
    mock_mongo.return_value = mock_client
    from app.common.responses import InternalServerErrorException

    with pytest.raises(InternalServerErrorException) as exc:
        await sync_strava_routes(mock_request, mock_user, mock_strava_token)
    assert "Failed to connect to Strava database" in str(exc.value.detail)


@pytest.mark.asyncio
@patch("app.modules.strava.sync_routes.AsyncMongoClient")
@patch("app.modules.strava.sync_routes.StravaApi")
async def test_sync_strava_routes_strava_api_error(
    mock_strava_api, mock_mongo, mock_request, mock_user, mock_strava_token
):
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_activities_col = MagicMock()
    mock_sync_meta_col = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)

    def get_collection_side_effect(name):
        if name == StravaDbCollection.ACTIVITIES or name == "activities":
            return mock_activities_col
        if name == StravaDbCollection.SYNC_META or name == "sync_metadata":
            return mock_sync_meta_col
        raise KeyError(name)

    mock_db.get_collection.side_effect = get_collection_side_effect
    mock_mongo.return_value = mock_client

    user_sync_data = {"user_id": mock_user.id, "synced_ids": [], "last_synced": None}
    mock_sync_meta_col.find_one = AsyncMock(return_value=user_sync_data)
    mock_sync_meta_col.insert_one = AsyncMock()
    mock_activities_col.count_documents = AsyncMock(return_value=0)

    # StravaApi raises error on get_athlete
    mock_strava = MagicMock()
    mock_strava.get_athlete = AsyncMock(side_effect=Exception("strava api error"))
    mock_strava_api.return_value = mock_strava

    from app.common.responses import InternalServerErrorException

    with pytest.raises(InternalServerErrorException) as exc:
        await sync_strava_routes(mock_request, mock_user, mock_strava_token)
    assert "Could not finish syncing routes from Strava" in str(exc.value.detail)
    assert "strava api error" in str(exc.value.detail)
