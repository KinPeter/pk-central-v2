import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.start_settings.update_start_settings import update_start_settings
from app.common.responses import NotFoundException, InternalServerErrorException
from app.modules.start_settings.start_settings_types import (
    StartSettingsRequest,
    StartSettings,
)


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


@pytest.fixture
def mock_body():
    body = MagicMock(spec=StartSettingsRequest)
    body.model_dump.return_value = {"name": "UpdatedName"}
    return body


@pytest.mark.asyncio
async def test_update_start_settings_success(mock_request, mock_user, mock_body):
    update_result = MagicMock()
    update_result.matched_count = 1
    updated_data = {
        "id": "cfg1",
        "created_at": "2024-01-01T00:00:00Z",
        "name": "UpdatedName",
        "shortcut_icon_base_url": "http://icons/",
        "strava_redirect_uri": "http://strava/",
        "user_id": mock_user.id,
    }
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(return_value=update_result)
    collection.find_one = AsyncMock(return_value=updated_data)

    result = await update_start_settings(mock_request, mock_body, mock_user)
    assert isinstance(result, StartSettings)
    assert result.name == "UpdatedName"
    assert result.id == "cfg1"
    assert result.open_weather_api_key == "owm-key"
    assert result.location_iq_api_key == "liq-key"
    assert result.unsplash_api_key == "unspl-key"
    assert result.strava_client_id == "strava-id"
    assert result.strava_client_secret == "strava-secret"


@pytest.mark.asyncio
async def test_update_start_settings_not_found(mock_request, mock_user, mock_body):
    update_result = MagicMock()
    update_result.matched_count = 0
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(return_value=update_result)

    with pytest.raises(NotFoundException):
        await update_start_settings(mock_request, mock_body, mock_user)
    mock_request.app.state.logger.error.assert_called_with(
        f"Failed to update Start Settings for user {mock_user.id}"
    )


@pytest.mark.asyncio
async def test_update_start_settings_internal_error(mock_request, mock_user, mock_body):
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(side_effect=Exception("db error"))

    with pytest.raises(InternalServerErrorException):
        await update_start_settings(mock_request, mock_body, mock_user)
    mock_request.app.state.logger.error.assert_any_call(
        f"Error updating Start Settings for user {mock_user.id}: db error"
    )
