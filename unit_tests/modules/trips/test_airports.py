import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from app.modules.trips.airports import get_airport_data
from app.modules.trips.trips_types import AirportResponse
from app.common.responses import InternalServerErrorException, NotFoundException


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_collection():
    return AsyncMock()


@pytest.fixture
def mock_env():
    env = MagicMock()
    env.GEMINI_API_KEY = "test-key"
    return env


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_app(mock_db, mock_env, mock_logger):
    app = MagicMock()
    app.state.db = mock_db
    app.state.env = mock_env
    app.state.logger = mock_logger
    return app


@pytest.fixture
def req(mock_app):
    r = MagicMock(Request)
    r.app = mock_app
    return r


@pytest.mark.asyncio
@patch("app.modules.trips.airports.GeminiApi")
async def test_get_airport_data_success_db(
    mock_gemini_api, mock_db, mock_collection, mock_env, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find_one.return_value = {
        "iata": "BUD",
        "icao": "LHBP",
        "name": "Liszt Ferenc International Airport",
        "city": "Budapest",
        "country": "Hungary",
        "lat": 47.4369,
        "lng": 19.2551,
    }
    mock_gemini_instance = mock_gemini_api.return_value
    mock_gemini_instance.generate_json = AsyncMock()
    result = await get_airport_data(req, "BUD")
    assert isinstance(result, AirportResponse)
    assert result.iata == "BUD"
    mock_db.get_collection.assert_called_once_with(
        mock_db.get_collection.call_args[0][0]
    )
    mock_collection.find_one.assert_awaited_once_with({"iata": "BUD"})
    mock_gemini_instance.generate_json.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.modules.trips.airports.GeminiApi")
async def test_get_airport_data_success_gemini(
    mock_gemini_api, mock_db, mock_collection, mock_env, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find_one.return_value = None
    mock_gemini_instance = mock_gemini_api.return_value
    mock_gemini_instance.generate_json = AsyncMock(
        return_value={
            "iata": "BUD",
            "icao": "LHBP",
            "name": "Liszt Ferenc International Airport",
            "city": "Budapest",
            "country": "Hungary",
            "lat": 47.4369,
            "lng": 19.2551,
        }
    )
    result = await get_airport_data(req, "BUD")
    assert isinstance(result, AirportResponse)
    assert result.iata == "BUD"
    mock_db.get_collection.assert_called_once_with(
        mock_db.get_collection.call_args[0][0]
    )
    mock_collection.find_one.assert_awaited_once_with({"iata": "BUD"})
    mock_gemini_instance.generate_json.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.modules.trips.airports.GeminiApi")
async def test_get_airport_data_incomplete_gemini(
    mock_gemini_api, mock_db, mock_collection, mock_env, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find_one.return_value = None
    mock_gemini_instance = mock_gemini_api.return_value
    mock_gemini_instance.generate_json = AsyncMock(
        return_value={
            "iata": "BUD",
            "icao": "LHBP",
            "name": "Liszt Ferenc International Airport",
            "city": "Budapest",
            "country": "Hungary",
        }
    )
    with pytest.raises(NotFoundException):
        await get_airport_data(req, "BUD")
    mock_logger.error.assert_called()
    mock_gemini_instance.generate_json.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.modules.trips.airports.GeminiApi")
async def test_get_airport_data_db_internal_error(
    mock_gemini_api, mock_db, mock_collection, mock_env, mock_logger, mock_app, req
):
    mock_gemini_instance = mock_gemini_api.return_value
    mock_gemini_instance.generate_json = AsyncMock()
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find_one.side_effect = Exception("DB error")
    with pytest.raises(InternalServerErrorException):
        await get_airport_data(req, "BUD")
    mock_logger.error.assert_called()
    mock_gemini_instance.generate_json.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.modules.trips.airports.GeminiApi")
async def test_get_airport_data_gemini_internal_error(
    mock_gemini_api, mock_db, mock_collection, mock_env, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find_one.return_value = None
    mock_gemini_instance = mock_gemini_api.return_value
    mock_gemini_instance.generate_json = AsyncMock()
    mock_gemini_instance.generate_json.side_effect = Exception("Gemini error")
    with pytest.raises(InternalServerErrorException):
        await get_airport_data(req, "BUD")
    mock_logger.error.assert_called()
    mock_gemini_instance.generate_json.assert_awaited_once()
