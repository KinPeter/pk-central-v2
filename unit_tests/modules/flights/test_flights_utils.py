import pytest

from app.modules.flights.flights_utils import to_flight
from app.modules.flights.flights_types import Flight


from app.modules.flights.flights_types import (
    Airport,
    Aircraft,
    Airline,
    Flight,
    SeatType,
    FlightClass,
    FlightReason,
    FlightRequest,
)


class TestToFlight:
    @pytest.mark.parametrize(
        "item,expected",
        [
            # All fields present
            (
                {
                    "id": "f1",
                    "flight_number": "LH123",
                    "date": "2024-01-01",
                    "departure_airport": Airport(
                        iata="FRA",
                        icao="EDDF",
                        name="Frankfurt",
                        city="Frankfurt",
                        country="Germany",
                        lat=50.0379,
                        lng=8.5622,
                    ),
                    "arrival_airport": Airport(
                        iata="JFK",
                        icao="KJFK",
                        name="JFK",
                        city="New York",
                        country="USA",
                        lat=40.6413,
                        lng=-73.7781,
                    ),
                    "departure_time": "10:00",
                    "arrival_time": "13:00",
                    "duration": "08:00",
                    "distance": 6200.0,
                    "airline": Airline(iata="LH", icao="DLH", name="Lufthansa"),
                    "aircraft": Aircraft(icao="A388", name="Airbus A380"),
                    "registration": "D-AIMA",
                    "seat_number": "12A",
                    "seat_type": SeatType.WINDOW,
                    "flight_class": FlightClass.BUSINESS,
                    "flight_reason": FlightReason.BUSINESS,
                    "note": "Work trip",
                    "is_planned": True,
                },
                Flight(
                    id="f1",
                    flight_number="LH123",
                    date="2024-01-01",
                    departure_airport=Airport(
                        iata="FRA",
                        icao="EDDF",
                        name="Frankfurt",
                        city="Frankfurt",
                        country="Germany",
                        lat=50.0379,
                        lng=8.5622,
                    ),
                    arrival_airport=Airport(
                        iata="JFK",
                        icao="KJFK",
                        name="JFK",
                        city="New York",
                        country="USA",
                        lat=40.6413,
                        lng=-73.7781,
                    ),
                    departure_time="10:00",
                    arrival_time="13:00",
                    duration="08:00",
                    distance=6200.0,
                    airline=Airline(iata="LH", icao="DLH", name="Lufthansa"),
                    aircraft=Aircraft(icao="A388", name="Airbus A380"),
                    registration="D-AIMA",
                    seat_number="12A",
                    seat_type=SeatType.WINDOW,
                    flight_class=FlightClass.BUSINESS,
                    flight_reason=FlightReason.BUSINESS,
                    note="Work trip",
                    is_planned=True,
                ),
            ),
            # Only required fields, optionals missing
            (
                {
                    "id": "f2",
                    "flight_number": "BA456",
                    "date": "2024-02-02",
                    "departure_airport": Airport(
                        iata="LHR",
                        icao="EGLL",
                        name="Heathrow",
                        city="London",
                        country="UK",
                        lat=51.4700,
                        lng=-0.4543,
                    ),
                    "arrival_airport": Airport(
                        iata="CDG",
                        icao="LFPG",
                        name="Charles de Gaulle",
                        city="Paris",
                        country="France",
                        lat=49.0097,
                        lng=2.5479,
                    ),
                    "departure_time": "09:00",
                    "arrival_time": "11:20",
                    "duration": "01:20",
                    "distance": 344.0,
                    "airline": Airline(iata="BA", icao="BAW", name="British Airways"),
                    "aircraft": Aircraft(icao="A320", name="Airbus A320"),
                    # registration, seat_number, seat_type, flight_class, flight_reason, note, is_planned missing
                },
                Flight(
                    id="f2",
                    flight_number="BA456",
                    date="2024-02-02",
                    departure_airport=Airport(
                        iata="LHR",
                        icao="EGLL",
                        name="Heathrow",
                        city="London",
                        country="UK",
                        lat=51.4700,
                        lng=-0.4543,
                    ),
                    arrival_airport=Airport(
                        iata="CDG",
                        icao="LFPG",
                        name="Charles de Gaulle",
                        city="Paris",
                        country="France",
                        lat=49.0097,
                        lng=2.5479,
                    ),
                    departure_time="09:00",
                    arrival_time="11:20",
                    duration="01:20",
                    distance=344.0,
                    airline=Airline(iata="BA", icao="BAW", name="British Airways"),
                    aircraft=Aircraft(icao="A320", name="Airbus A320"),
                    registration=None,
                    seat_number=None,
                    seat_type=None,
                    flight_class=None,
                    flight_reason=None,
                    note=None,
                    is_planned=False,
                ),
            ),
        ],
    )
    def test_to_flight(self, item, expected):
        result = to_flight(item)
        assert isinstance(result, Flight)
        assert result.id == expected.id
        assert result.flight_number == expected.flight_number
        assert result.date == expected.date
        assert result.departure_airport == expected.departure_airport
        assert result.arrival_airport == expected.arrival_airport
        assert result.departure_time == expected.departure_time
        assert result.arrival_time == expected.arrival_time
        assert result.duration == expected.duration
        assert result.distance == expected.distance
        assert result.airline == expected.airline
        assert result.aircraft == expected.aircraft
        assert result.registration == expected.registration
        assert result.seat_number == expected.seat_number
        assert result.seat_type == expected.seat_type
        assert result.flight_class == expected.flight_class
        assert result.flight_reason == expected.flight_reason
        assert result.note == expected.note
        assert result.is_planned == expected.is_planned


# ── Shared fixtures for upsert tests ─────────────────────────────────────────

AIRPORT_FRA = Airport(iata="FRA", icao="EDDF", name="Frankfurt Airport", city="Frankfurt", country="Germany", lat=50.0379, lng=8.5622)
AIRPORT_JFK = Airport(iata="JFK", icao="KJFK", name="JFK Airport", city="New York", country="USA", lat=40.6413, lng=-73.7781)


def make_flight_request(dep: Airport = AIRPORT_FRA, arr: Airport = AIRPORT_JFK) -> FlightRequest:
    return FlightRequest(
        flight_number="LH001",
        date="2024-03-15",
        departure_airport=dep,
        arrival_airport=arr,
        departure_time="10:00",
        arrival_time="18:00",
        duration="08:00",
        distance=6200.0,
        airline=Airline(iata="LH", icao="DLH", name="Lufthansa"),
        aircraft=Aircraft(icao="A388", name="Airbus A380"),
    )


# ── _upsert_airports ──────────────────────────────────────────────────────────

class TestUpsertAirports:
    @pytest.mark.asyncio
    async def test_upserts_both_airports(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock
        from app.modules.flights.flights_utils import _upsert_airports

        collection = MagicMock()
        inserted_result = MagicMock(upserted_id="new-id")
        collection.update_one = AsyncMock(return_value=inserted_result)

        db = MagicMock()
        db.get_collection.return_value = collection
        logger = MagicMock()

        await _upsert_airports(db, make_flight_request(), logger)

        assert collection.update_one.call_count == 2

    @pytest.mark.asyncio
    async def test_uses_setOnInsert_operator(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock, call
        from app.modules.flights.flights_utils import _upsert_airports

        collection = MagicMock()
        collection.update_one = AsyncMock(return_value=MagicMock(upserted_id=None))

        db = MagicMock()
        db.get_collection.return_value = collection
        logger = MagicMock()

        await _upsert_airports(db, make_flight_request(), logger)

        for c in collection.update_one.call_args_list:
            _, update_doc, *_ = c.args
            assert "$setOnInsert" in update_doc
            assert "$set" not in update_doc

    @pytest.mark.asyncio
    async def test_filters_by_iata(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.modules.flights.flights_utils import _upsert_airports

        collection = MagicMock()
        collection.update_one = AsyncMock(return_value=MagicMock(upserted_id=None))

        db = MagicMock()
        db.get_collection.return_value = collection
        logger = MagicMock()

        await _upsert_airports(db, make_flight_request(), logger)

        calls = collection.update_one.call_args_list
        assert calls[0].args[0] == {"iata": "FRA"}
        assert calls[1].args[0] == {"iata": "JFK"}

    @pytest.mark.asyncio
    async def test_logs_info_when_new_airport_inserted(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.modules.flights.flights_utils import _upsert_airports

        collection = MagicMock()
        collection.update_one = AsyncMock(return_value=MagicMock(upserted_id="new-id"))

        db = MagicMock()
        db.get_collection.return_value = collection
        logger = MagicMock()

        await _upsert_airports(db, make_flight_request(), logger)

        info_messages = [str(c.args[0]) for c in logger.info.call_args_list]
        assert any("New airport added" in m and "FRA" in m for m in info_messages)
        assert any("New airport added" in m and "JFK" in m for m in info_messages)

    @pytest.mark.asyncio
    async def test_logs_info_when_airport_already_exists(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.modules.flights.flights_utils import _upsert_airports

        collection = MagicMock()
        collection.update_one = AsyncMock(return_value=MagicMock(upserted_id=None))

        db = MagicMock()
        db.get_collection.return_value = collection
        logger = MagicMock()

        await _upsert_airports(db, make_flight_request(), logger)

        info_messages = [str(c.args[0]) for c in logger.info.call_args_list]
        assert any("already exists" in m and "FRA" in m for m in info_messages)
        assert any("already exists" in m and "JFK" in m for m in info_messages)

    @pytest.mark.asyncio
    async def test_logs_error_on_db_exception(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.modules.flights.flights_utils import _upsert_airports

        collection = MagicMock()
        collection.update_one = AsyncMock(side_effect=Exception("db down"))

        db = MagicMock()
        db.get_collection.return_value = collection
        logger = MagicMock()

        # should not raise
        await _upsert_airports(db, make_flight_request(), logger)

        logger.error.assert_called_once()
        assert "db down" in str(logger.error.call_args.args[0])
