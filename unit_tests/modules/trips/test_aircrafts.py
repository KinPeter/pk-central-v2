import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from app.modules.trips.aircrafts import search_aircrafts
from app.modules.flights.flights_types import Aircraft
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
async def test_search_aircrafts_success_name(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_find_result = MagicMock()
    mock_find_result.to_list = AsyncMock(
        return_value=[{"name": "Boeing 737", "icao": "B737"}]
    )
    mock_collection.find.return_value = mock_find_result
    result = await search_aircrafts(req, query="Boeing")
    assert isinstance(result, ListResponse)
    assert len(result.entities) == 1
    assert result.entities[0].name == "Boeing 737"
    mock_db.get_collection.assert_called_once()
    mock_collection.find.assert_called_once_with(
        {
            "$or": [
                {"name": {"$regex": "Boeing", "$options": "i"}},
                {"icao": {"$regex": "Boeing", "$options": "i"}},
            ]
        }
    )
    mock_logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_search_aircrafts_success_icao(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_find_result = MagicMock()
    mock_find_result.to_list = AsyncMock(
        return_value=[{"name": "Airbus A320", "icao": "A320"}]
    )
    mock_collection.find.return_value = mock_find_result
    result = await search_aircrafts(req, query="A320")
    assert isinstance(result, ListResponse)
    assert len(result.entities) == 1
    assert result.entities[0].icao == "A320"
    mock_db.get_collection.assert_called_once()
    mock_collection.find.assert_called_once_with(
        {
            "$or": [
                {"name": {"$regex": "A320", "$options": "i"}},
                {"icao": {"$regex": "A320", "$options": "i"}},
            ]
        }
    )
    mock_logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_search_aircrafts_no_results(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_find_result = MagicMock()
    mock_find_result.to_list = AsyncMock(return_value=[])
    mock_collection.find.return_value = mock_find_result
    result = await search_aircrafts(req, query="Unknown")
    assert isinstance(result, ListResponse)
    assert result.entities == []
    mock_logger.info.assert_called_once()


@pytest.mark.asyncio
async def test_search_aircrafts_error(
    mock_db, mock_collection, mock_logger, mock_app, req
):
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.side_effect = Exception("DB error")
    with pytest.raises(InternalServerErrorException):
        await search_aircrafts(req, query="Boeing")
    mock_logger.error.assert_called_once()
