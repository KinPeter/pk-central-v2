import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.start_settings.get_start_settings import get_start_settings
from app.common.responses import NotFoundException, InternalServerErrorException
from app.modules.start_settings.start_settings_types import StartSettings


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.db = MagicMock()
    req.app.state.logger = MagicMock()
    req.app.state.env = MagicMock()
    req.app.state.env.OPEN_WEATHER_MAP_API_KEY = "owm-key"
    req.app.state.env.LOCATION_IQ_API_KEY = "liq-key"
    req.app.state.env.UNSPLASH_API_KEY = "unspl-key"
    req.app.state.env.STRAVA_CLIENT_ID = "strava-id"
    req.app.state.env.STRAVA_CLIENT_SECRET = "strava-secret"
    return req


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user123"
    return user


@pytest.mark.asyncio
async def test_get_start_settings_success(mock_request, mock_user):
    data = {
        "id": "cfg1",
        "created_at": "2024-01-01T00:00:00Z",
        "name": "MyName",
        "shortcut_icon_base_url": "http://icons/",
        "strava_redirect_uri": "http://strava/",
        "user_id": mock_user.id,
    }
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        return_value=data
    )
    result = await get_start_settings(mock_request, mock_user)
    assert isinstance(result, StartSettings)
    assert result.id == "cfg1"
    assert result.name == "MyName"
    assert result.shortcut_icon_base_url == "http://icons/"
    assert result.strava_redirect_uri == "http://strava/"
    assert result.open_weather_api_key == "owm-key"
    assert result.location_iq_api_key == "liq-key"
    assert result.unsplash_api_key == "unspl-key"
    assert result.strava_client_id == "strava-id"
    assert result.strava_client_secret == "strava-secret"


@pytest.mark.asyncio
async def test_get_start_settings_not_found(mock_request, mock_user):
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        return_value=None
    )
    with pytest.raises(NotFoundException):
        await get_start_settings(mock_request, mock_user)
    mock_request.app.state.logger.error.assert_called_with(
        f"Start Settings not found for user {mock_user.id}"
    )


@pytest.mark.asyncio
async def test_get_start_settings_internal_error(mock_request, mock_user):
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        side_effect=Exception("db error")
    )
    with pytest.raises(InternalServerErrorException):
        await get_start_settings(mock_request, mock_user)
    mock_request.app.state.logger.error.assert_any_call(
        f"Error retrieving Start Settings for user {mock_user.id}: db error"
    )
