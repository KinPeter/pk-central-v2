import pytest
from datetime import datetime
from pymongo.server_api import ServerApi
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.strava.create_routemap import create_routemap
from app.modules.strava.strava_types import StravaActivityType, StravaRoutemap


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


dummy_map = StravaRoutemap(count=0, points=set())
mock_activities = [
    {"user_id": "user123", "type": "Run", "start_date": datetime(2024, 1, 1)},
    {"user_id": "user123", "type": "Walk", "start_date": datetime(2024, 1, 1)},
]


@pytest.mark.asyncio
@patch("app.modules.strava.create_routemap.AsyncMongoClient")
@patch("app.modules.strava.create_routemap.generate_routemap", return_value=dummy_map)
async def test_create_routemap_success(
    mock_generate_routemap, mock_mongo, mock_request, mock_user
):
    before = datetime(2024, 1, 1)
    after = datetime(2023, 1, 1)
    types = None

    # Mock MongoDB client and collection
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.return_value.to_list = AsyncMock(return_value=mock_activities)
    mock_mongo.return_value = mock_client

    result = await create_routemap(mock_request, mock_user, before, after, types)
    mock_client.admin.command.assert_called_once_with("ping")
    mock_db.get_collection.assert_called_once_with("activities")
    mock_collection.find.assert_called_once_with(
        {
            "user_id": mock_user.id,
            "type": {"$in": ["Walk", "Run", "Ride"]},
            "start_date": {"$gte": after, "$lte": before},
        }
    )
    mock_generate_routemap.assert_called_once_with(
        activities=mock_activities,
        logger=mock_request.app.state.logger,
        sampling_rate=1,
    )
    assert result.routemap == dummy_map
    assert result.activity_count == 2
    assert set(result.types) == {"Run", "Walk"}
    assert result.after == after.isoformat()
    assert result.before == before.isoformat()


@pytest.mark.asyncio
@patch("app.modules.strava.create_routemap.AsyncMongoClient")
@patch("app.modules.strava.create_routemap.generate_routemap", return_value=dummy_map)
async def test_create_routemap_no_before_no_after(
    mock_generate_routemap, mock_mongo, mock_request, mock_user
):
    before = None
    after = None
    types = None
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.return_value.to_list = AsyncMock(return_value=mock_activities)
    mock_mongo.return_value = mock_client

    result = await create_routemap(mock_request, mock_user, before, after, types)
    filter_query = {
        "user_id": mock_user.id,
        "type": {"$in": ["Walk", "Run", "Ride"]},
    }
    mock_collection.find.assert_called_once_with(filter_query)
    assert result.routemap == dummy_map
    assert result.activity_count == 2


@pytest.mark.asyncio
@patch("app.modules.strava.create_routemap.AsyncMongoClient")
@patch("app.modules.strava.create_routemap.generate_routemap", return_value=dummy_map)
async def test_create_routemap_only_before(
    mock_generate_routemap, mock_mongo, mock_request, mock_user
):
    before = datetime(2024, 1, 1)
    after = None
    types = None
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.return_value.to_list = AsyncMock(return_value=mock_activities)
    mock_mongo.return_value = mock_client

    result = await create_routemap(mock_request, mock_user, before, after, types)
    filter_query = {
        "user_id": mock_user.id,
        "type": {"$in": ["Walk", "Run", "Ride"]},
        "start_date": {"$lte": before},
    }
    mock_collection.find.assert_called_once_with(filter_query)
    assert result.routemap == dummy_map
    assert result.activity_count == 2


@pytest.mark.asyncio
@patch("app.modules.strava.create_routemap.AsyncMongoClient")
@patch("app.modules.strava.create_routemap.generate_routemap", return_value=dummy_map)
async def test_create_routemap_only_after(
    mock_generate_routemap, mock_mongo, mock_request, mock_user
):
    before = None
    after = datetime(2023, 1, 1)
    types = None
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.return_value.to_list = AsyncMock(return_value=mock_activities)
    mock_mongo.return_value = mock_client

    result = await create_routemap(mock_request, mock_user, before, after, types)
    filter_query = {
        "user_id": mock_user.id,
        "type": {"$in": ["Walk", "Run", "Ride"]},
        "start_date": {"$gte": after},
    }
    mock_collection.find.assert_called_once_with(filter_query)
    assert result.routemap == dummy_map
    assert result.activity_count == 2


@pytest.mark.asyncio
@patch("app.modules.strava.create_routemap.AsyncMongoClient")
@patch("app.modules.strava.create_routemap.generate_routemap", return_value=dummy_map)
async def test_create_routemap_with_types(
    mock_generate_routemap, mock_mongo, mock_request, mock_user
):
    before = datetime(2024, 1, 1)
    after = datetime(2023, 1, 1)
    types = [StravaActivityType.RUN, StravaActivityType.WALK]
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.return_value.to_list = AsyncMock(return_value=mock_activities)
    mock_mongo.return_value = mock_client

    result = await create_routemap(mock_request, mock_user, before, after, types)
    filter_query = {
        "user_id": mock_user.id,
        "type": {"$in": [t.value for t in types]},
        "start_date": {"$gte": after, "$lte": before},
    }
    mock_collection.find.assert_called_once_with(filter_query)
    assert result.routemap == dummy_map
    assert result.activity_count == 2


@pytest.mark.asyncio
@patch("app.modules.strava.create_routemap.AsyncMongoClient")
async def test_create_routemap_db_connection_error(mock_mongo, mock_request, mock_user):
    before = datetime(2024, 1, 1)
    after = datetime(2023, 1, 1)
    types = None
    mock_client = AsyncMock()
    mock_client.admin.command = AsyncMock(side_effect=Exception("db down"))
    mock_mongo.return_value = mock_client

    from app.common.responses import InternalServerErrorException

    with pytest.raises(InternalServerErrorException) as exc:
        await create_routemap(mock_request, mock_user, before, after, types)
    assert "Failed to connect to Strava database" in str(exc.value.detail)


@pytest.mark.asyncio
@patch("app.modules.strava.create_routemap.AsyncMongoClient")
@patch("app.modules.strava.create_routemap.generate_routemap", return_value=dummy_map)
async def test_create_routemap_db_query_error(
    mock_generate_routemap, mock_mongo, mock_request, mock_user
):
    before = datetime(2024, 1, 1)
    after = datetime(2023, 1, 1)
    types = None
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.return_value.to_list = AsyncMock(
        side_effect=Exception("query error")
    )
    mock_mongo.return_value = mock_client

    from app.common.responses import InternalServerErrorException

    with pytest.raises(InternalServerErrorException) as exc:
        await create_routemap(mock_request, mock_user, before, after, types)
    assert "Could not create routemap" in str(exc.value.detail)


@pytest.mark.asyncio
@patch("app.modules.strava.create_routemap.AsyncMongoClient")
@patch("app.modules.strava.create_routemap.generate_routemap", return_value=dummy_map)
async def test_create_routemap_empty_response(
    mock_generate_routemap, mock_mongo, mock_request, mock_user
):
    before = datetime(2024, 1, 1)
    after = datetime(2023, 1, 1)
    types = None
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client.admin.command = AsyncMock()
    mock_client.get_database = MagicMock(return_value=mock_db)
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
    mock_mongo.return_value = mock_client

    result = await create_routemap(mock_request, mock_user, before, after, types)
    assert result.routemap is None
    assert result.activity_count == 0
    assert result.types == []
