import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from app.modules.trips.airlines import search_airlines
from app.modules.flights.flights_types import Airline
from app.common.responses import InternalServerErrorException, ListResponse


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_collection():
    return MagicMock()


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_app(mock_db, mock_logger):
    app = MagicMock()
    app.state.db = mock_db
    app.state.logger = mock_logger
    return app


@pytest.fixture
def req(mock_app):
    r = MagicMock(Request)
    r.app = mock_app
    return r


@pytest.mark.asyncio
async def test_search_airlines_iata_success(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_find_result = MagicMock()
    mock_find_result.to_list = AsyncMock(
        return_value=[{"iata": "LH", "icao": "DLH", "name": "Lufthansa"}]
    )
    mock_collection.find.return_value = mock_find_result
    result = await search_airlines(req, iata="LH", name=None)
    assert isinstance(result, ListResponse)
    assert len(result.entities) == 1
    assert result.entities[0].iata == "LH"
    mock_db.get_collection.assert_called_once()
    mock_collection.find.assert_called_once_with(
        {"iata": {"$regex": "LH", "$options": "i"}}
    )
    mock_logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_search_airlines_name_success(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_find_result = MagicMock()
    mock_find_result.to_list = AsyncMock(
        return_value=[{"iata": "BA", "icao": "BAW", "name": "British Airways"}]
    )
    mock_collection.find.return_value = mock_find_result
    result = await search_airlines(req, iata=None, name="British")
    assert isinstance(result, ListResponse)
    assert len(result.entities) == 1
    assert result.entities[0].name == "British Airways"
    mock_db.get_collection.assert_called_once()
    mock_collection.find.assert_called_once_with(
        {"name": {"$regex": "British", "$options": "i"}}
    )
    mock_logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_search_airlines_both_iata_and_name_prioritizes_iata(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_find_result = MagicMock()
    mock_find_result.to_list = AsyncMock(
        return_value=[{"iata": "LH", "icao": "DLH", "name": "Lufthansa"}]
    )
    mock_collection.find.return_value = mock_find_result
    result = await search_airlines(req, iata="LH", name="Lufthansa")
    assert isinstance(result, ListResponse)
    assert len(result.entities) == 1
    assert result.entities[0].iata == "LH"
    mock_db.get_collection.assert_called_once()
    mock_collection.find.assert_called_once_with(
        {"iata": {"$regex": "LH", "$options": "i"}}
    )
    mock_logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_search_airlines_no_query_returns_empty(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    result = await search_airlines(req, iata=None, name=None)
    assert isinstance(result, ListResponse)
    assert result.entities == []
    mock_db.get_collection.assert_not_called()
    mock_logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_search_airlines_no_results(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_find_result = MagicMock()
    mock_find_result.to_list = AsyncMock(return_value=[])
    mock_collection.find.return_value = mock_find_result
    result = await search_airlines(req, iata="XX", name=None)
    assert isinstance(result, ListResponse)
    assert result.entities == []
    mock_logger.info.assert_called_once()


@pytest.mark.asyncio
async def test_search_airlines_error(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.side_effect = Exception("DB error")
    with pytest.raises(InternalServerErrorException):
        await search_airlines(req, iata="LH", name=None)
    mock_logger.error.assert_called_once()
