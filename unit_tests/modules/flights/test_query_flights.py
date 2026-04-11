import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from app.modules.flights.query_flights import query_flights
from app.modules.flights.flights_types import FlightClass, FlightQuery, FlightReason, SeatType
from app.common.responses import InternalServerErrorException, ListResponse


@pytest.fixture
def user():
    u = MagicMock()
    u.id = "user123"
    return u


@pytest.fixture
def logger():
    return MagicMock()


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def collection():
    return MagicMock()


@pytest.fixture
def req(db, logger):
    req = MagicMock(spec=Request)
    req.app.state.db = db
    req.app.state.logger = logger
    return req


@pytest.fixture
def flight_item():
    return {
        "id": "f1",
        "user_id": "user123",
        "flight_number": "LH100",
        "date": "2024-01-01",
        "departure_airport": {"iata": "FRA", "icao": "EDDF", "name": "Frankfurt", "city": "Frankfurt", "country": "Germany", "lat": 50.0, "lng": 8.0},
        "arrival_airport": {"iata": "JFK", "icao": "KJFK", "name": "JFK", "city": "New York", "country": "USA", "lat": 40.0, "lng": -73.0},
        "departure_time": "10:00",
        "arrival_time": "18:00",
        "duration": "08:00",
        "distance": 6200.0,
        "airline": {"iata": "LH", "icao": "DLH", "name": "Lufthansa"},
        "aircraft": {"icao": "A388", "name": "Airbus A380"},
        "seat_type": "Window",
        "flight_class": "Business",
        "flight_reason": "Business",
        "is_planned": False,
    }


@pytest.mark.asyncio
async def test_query_flights_no_filters(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    result = await query_flights(req, user, FlightQuery())

    assert isinstance(result, ListResponse)
    assert result.entities == [flight_item]
    collection.find.assert_called_once_with({"user_id": "user123"})


@pytest.mark.asyncio
async def test_query_flights_by_year_single(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(year=["2024"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "date": {"$regex": "^(2024)"},
    })


@pytest.mark.asyncio
async def test_query_flights_by_year_multiple(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(year=["2023", "2024"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "date": {"$regex": "^(2023|2024)"},
    })


@pytest.mark.asyncio
async def test_query_flights_by_is_planned(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(is_planned=True))

    collection.find.assert_called_once_with({"user_id": "user123", "is_planned": True})


@pytest.mark.asyncio
async def test_query_flights_by_flight_class(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(flight_class=[FlightClass.BUSINESS]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "flight_class": {"$in": ["Business"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_flight_reason(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(flight_reason=[FlightReason.LEISURE, FlightReason.CREW]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "flight_reason": {"$in": ["Leisure", "Crew"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_seat_type(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(seat_type=[SeatType.AISLE, SeatType.WINDOW]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "seat_type": {"$in": ["Aisle", "Window"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_airline_iata(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(airline_iata=["LH", "TK"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "airline.iata": {"$in": ["LH", "TK"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_aircraft_icao(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(aircraft_icao=["A388"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "aircraft.icao": {"$in": ["A388"]},
    })


@pytest.mark.asyncio
async def test_query_flights_distance_gt(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(distance_gt=5000.0))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "distance": {"$gt": 5000.0},
    })


@pytest.mark.asyncio
async def test_query_flights_distance_lt(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(distance_lt=1000.0))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "distance": {"$lt": 1000.0},
    })


@pytest.mark.asyncio
async def test_query_flights_distance_range(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(distance_gt=500.0, distance_lt=7000.0))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "distance": {"$gt": 500.0, "$lt": 7000.0},
    })


@pytest.mark.asyncio
async def test_query_flights_by_to_city(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(to_city=["New York"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "arrival_airport.city": {"$in": ["New York"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_to_country(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(to_country=["USA"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "arrival_airport.country": {"$in": ["USA"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_to_airport_iata(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(to_airport_iata=["JFK"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "arrival_airport.iata": {"$in": ["JFK"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_from_city(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(from_city=["Frankfurt"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "departure_airport.city": {"$in": ["Frankfurt"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_from_country(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(from_country=["Germany"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "departure_airport.country": {"$in": ["Germany"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_from_airport_iata(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(from_airport_iata=["FRA"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "departure_airport.iata": {"$in": ["FRA"]},
    })


@pytest.mark.asyncio
async def test_query_flights_by_city_either(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(city=["Frankfurt"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "$and": [
            {"$or": [
                {"departure_airport.city": {"$in": ["Frankfurt"]}},
                {"arrival_airport.city": {"$in": ["Frankfurt"]}},
            ]}
        ],
    })


@pytest.mark.asyncio
async def test_query_flights_by_country_either(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(country=["Germany"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "$and": [
            {"$or": [
                {"departure_airport.country": {"$in": ["Germany"]}},
                {"arrival_airport.country": {"$in": ["Germany"]}},
            ]}
        ],
    })


@pytest.mark.asyncio
async def test_query_flights_by_airport_iata_either(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(airport_iata=["FRA", "JFK"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "$and": [
            {"$or": [
                {"departure_airport.iata": {"$in": ["FRA", "JFK"]}},
                {"arrival_airport.iata": {"$in": ["FRA", "JFK"]}},
            ]}
        ],
    })


@pytest.mark.asyncio
async def test_query_flights_multiple_either_filters(monkeypatch, user, req, db, collection, flight_item):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[flight_item])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    await query_flights(req, user, FlightQuery(city=["Frankfurt"], country=["Germany"]))

    collection.find.assert_called_once_with({
        "user_id": "user123",
        "$and": [
            {"$or": [
                {"departure_airport.city": {"$in": ["Frankfurt"]}},
                {"arrival_airport.city": {"$in": ["Frankfurt"]}},
            ]},
            {"$or": [
                {"departure_airport.country": {"$in": ["Germany"]}},
                {"arrival_airport.country": {"$in": ["Germany"]}},
            ]},
        ],
    })


@pytest.mark.asyncio
async def test_query_flights_empty_result(monkeypatch, user, req, db, collection):
    db.get_collection.return_value = collection
    collection.find.return_value.to_list = AsyncMock(return_value=[])
    monkeypatch.setattr("app.modules.flights.query_flights.to_flight", lambda x: x)

    result = await query_flights(req, user, FlightQuery(year=["1999"]))

    assert isinstance(result, ListResponse)
    assert result.entities == []


@pytest.mark.asyncio
async def test_query_flights_db_error(user, req, db, logger):
    db.get_collection.side_effect = Exception("db error")

    with pytest.raises(InternalServerErrorException) as exc_info:
        await query_flights(req, user, FlightQuery())

    assert "db error" in str(exc_info.value)
    logger.error.assert_called()
