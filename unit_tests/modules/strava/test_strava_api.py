import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.strava.strava_api import StravaApi


@pytest.fixture
def logger():
    return MagicMock()


@pytest.fixture
def strava_api(logger):
    return StravaApi(access_token="dummy_token", logger=logger)


@pytest.mark.asyncio
async def test_get_athlete_calls_get_request(strava_api):
    strava_api._get_request = AsyncMock(return_value={"id": 123})
    result = await strava_api.get_athlete()
    strava_api._get_request.assert_awaited_once_with("/athlete")
    assert result == {"id": 123}


@pytest.mark.asyncio
async def test_get_activities_calls_get_request_with_params(strava_api):
    strava_api._get_request = AsyncMock(return_value=[{"id": 1}])
    result = await strava_api.get_activities(page=2, per_page=10, after=100, before=200)
    strava_api._get_request.assert_awaited_once_with(
        "/athlete/activities",
        params={"page": 2, "per_page": 10, "after": 100, "before": 200},
    )
    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_get_all_activities_paginates(strava_api):
    # First call returns activities, second call returns empty list
    strava_api.get_activities = AsyncMock(side_effect=[[{"id": 1}], []])
    result = await strava_api.get_all_activities()
    assert strava_api.get_activities.await_count == 2
    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_get_activity_latlng_stream_calls_get_request(strava_api):
    strava_api._get_request = AsyncMock(return_value={"latlng": []})
    result = await strava_api.get_activity_latlng_stream(42)
    strava_api._get_request.assert_awaited_once_with(
        "/activities/42/streams", params={"keys": "latlng", "key_by_type": "true"}
    )
    assert result == {"latlng": []}


@pytest.mark.asyncio
@patch("app.modules.strava.strava_api.httpx.AsyncClient")
async def test__get_request_success(mock_async_client, strava_api, logger):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"foo": "bar"}
    mock_async_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=mock_response
    )
    result = await strava_api._get_request("/athlete")
    assert result == {"foo": "bar"}
    logger.info.assert_called()


@pytest.mark.asyncio
@patch("app.modules.strava.strava_api.httpx.AsyncClient")
async def test__get_request_http_error(mock_async_client, strava_api, logger):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("error")
    mock_response.json.return_value = None
    mock_response.status_code = 400
    mock_response.text = "bad request"
    mock_async_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=mock_response
    )
    with patch("app.modules.strava.strava_api.HTTPException") as mock_http_exc:
        mock_http_exc.side_effect = lambda status_code, detail: Exception(
            f"HTTP {status_code}: {detail}"
        )
        with pytest.raises(Exception, match="error"):
            await strava_api._get_request("/athlete")
            logger.error.assert_called()
