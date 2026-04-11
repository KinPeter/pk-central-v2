import asyncio
from logging import Logger

from app.common.db import DbCollection
from app.common.types import AsyncDatabase
from app.modules.flights.flights_types import Flight, FlightRequest


async def _upsert_airports(db: AsyncDatabase, body: FlightRequest, logger: Logger) -> None:
    """Upsert departure and arrival airports into the airports collection."""
    try:
        collection = db.get_collection(DbCollection.AIRPORTS)
        for airport in (body.departure_airport, body.arrival_airport):
            logger.info(f"Upserting airport: {airport.iata} ({airport.name})")
            airport_doc = airport.model_dump(mode="json")
            result = await collection.update_one(
                {"iata": airport.iata},
                {"$setOnInsert": airport_doc},
                upsert=True,
            )
            if result.upserted_id is not None:
                logger.info(f"New airport added: {airport.iata} ({airport.name})")
            else:
                logger.info(f"Airport already exists, skipping: {airport.iata} ({airport.name})")
    except Exception as e:
        # Log the error but don't raise it, since this is a background task and we don't want to affect the main flow
        logger.error(f"Failed to upsert airports for flight: {e}")


def upsert_airports_from_flight(db: AsyncDatabase, body: FlightRequest, logger: Logger) -> None:
    """Schedule airport upserts as a fire-and-forget background task."""
    asyncio.create_task(_upsert_airports(db, body, logger))


def to_flight(item: dict) -> Flight:
    return Flight(
        id=item["id"],
        flight_number=item["flight_number"],
        date=item["date"],
        departure_airport=item["departure_airport"],
        arrival_airport=item["arrival_airport"],
        departure_time=item["departure_time"],
        arrival_time=item["arrival_time"],
        duration=item["duration"],
        distance=item["distance"],
        airline=item["airline"],
        aircraft=item["aircraft"],
        registration=item.get("registration"),
        seat_number=item.get("seat_number"),
        seat_type=item.get("seat_type"),
        flight_class=item.get("flight_class"),
        flight_reason=item.get("flight_reason"),
        note=item.get("note"),
        is_planned=item.get("is_planned", False),
    )
