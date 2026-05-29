import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from app.modules.activities.steps_sync_api import StepsSyncApi
from app.modules.activities.activities_types import StepsItem


@pytest.fixture
def api():
    env = MagicMock()
    env.STEPS_SYNC_URL = "https://example.com/steps"
    env.STEPS_SYNC_API_KEY = "test-api-key"
    logger = MagicMock()
    return StepsSyncApi(env, logger)


@pytest.fixture
def mock_httpx_client():
    """Return mocks for httpx.AsyncClient context manager."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"steps": 5000, "date": "2026-05-01"},
        {"steps": 6000, "date": "2026-05-02"},
    ]

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    return mock_context, mock_client, mock_response


@pytest.mark.asyncio
async def test_fetch_steps_no_dates(api, mock_httpx_client):
    """Only apiKey param sent, returns valid items."""
    mock_context, mock_client, mock_response = mock_httpx_client

    with patch("httpx.AsyncClient", return_value=mock_context):
        result = await api.fetch_steps()

    assert len(result) == 2
    assert result[0].steps == 5000
    assert result[0].date == "2026-05-01"
    assert result[1].steps == 6000
    assert result[1].date == "2026-05-02"

    mock_client.get.assert_called_once_with(
        "https://example.com/steps",
        params={"apiKey": "test-api-key"},
    )


@pytest.mark.asyncio
async def test_fetch_steps_with_from_date(api, mock_httpx_client):
    """from param included in request."""
    mock_context, mock_client, mock_response = mock_httpx_client
    mock_response.json.return_value = [{"steps": 7000, "date": "2026-05-21"}]

    with patch("httpx.AsyncClient", return_value=mock_context):
        result = await api.fetch_steps(from_date="2026-05-21")

    assert len(result) == 1
    assert result[0].steps == 7000

    mock_client.get.assert_called_once_with(
        "https://example.com/steps",
        params={"apiKey": "test-api-key", "from": "2026-05-21"},
    )


@pytest.mark.asyncio
async def test_fetch_steps_with_both_dates(api, mock_httpx_client):
    """Both from and to params present in request."""
    mock_context, mock_client, mock_response = mock_httpx_client

    with patch("httpx.AsyncClient", return_value=mock_context):
        result = await api.fetch_steps(from_date="2026-05-01", to_date="2026-05-07")

    mock_client.get.assert_called_once_with(
        "https://example.com/steps",
        params={"apiKey": "test-api-key", "from": "2026-05-01", "to": "2026-05-07"},
    )


@pytest.mark.asyncio
async def test_fetch_steps_http_4xx(api, mock_httpx_client):
    """API returns 403 → HTTPException with that status."""
    mock_context, mock_client, _ = mock_httpx_client

    error_response = MagicMock()
    error_response.status_code = 403
    error_response.text = "Forbidden"

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "403 Forbidden",
        request=MagicMock(),
        response=error_response,
    )
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)

    with patch("httpx.AsyncClient", return_value=mock_context):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await api.fetch_steps()

    assert exc_info.value.status_code == 403
    assert "StepsSync API error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_fetch_steps_http_5xx(api, mock_httpx_client):
    """API returns 502 → HTTPException."""
    mock_context, mock_client, _ = mock_httpx_client

    error_response = MagicMock()
    error_response.status_code = 502
    error_response.text = "Bad Gateway"

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "502 Bad Gateway",
        request=MagicMock(),
        response=error_response,
    )
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)

    with patch("httpx.AsyncClient", return_value=mock_context):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await api.fetch_steps()

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_fetch_steps_request_error(api, mock_httpx_client):
    """Network failure → HTTPException 500."""
    mock_context, mock_client, _ = mock_httpx_client

    mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection refused"))
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)

    with patch("httpx.AsyncClient", return_value=mock_context):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await api.fetch_steps()

    assert exc_info.value.status_code == 500
    assert "StepsSync API request failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_fetch_steps_unexpected_error(api, mock_httpx_client):
    """Response JSON is invalid → HTTPException 500."""
    mock_context, mock_client, mock_response = mock_httpx_client

    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)

    with patch("httpx.AsyncClient", return_value=mock_context):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await api.fetch_steps()

    assert exc_info.value.status_code == 500
    assert "Unexpected error" in exc_info.value.detail
