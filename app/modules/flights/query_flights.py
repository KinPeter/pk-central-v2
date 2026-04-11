from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, ListResponse
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import CurrentUser
from app.modules.flights.flights_types import Flight, FlightQuery
from app.modules.flights.flights_utils import to_flight


async def query_flights(
    request: Request,
    user: CurrentUser,
    body: FlightQuery,
) -> ListResponse[Flight]:
    db: AsyncDatabase = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.FLIGHTS)

        query: dict = {"user_id": user.id}

        if body.year:
            year_pattern = "|".join(body.year)
            query["date"] = {"$regex": f"^({year_pattern})"}

        if body.is_planned is not None:
            query["is_planned"] = body.is_planned

        if body.flight_class:
            query["flight_class"] = {"$in": [fc.value for fc in body.flight_class]}

        if body.flight_reason:
            query["flight_reason"] = {"$in": [fr.value for fr in body.flight_reason]}

        if body.seat_type:
            query["seat_type"] = {"$in": [st.value for st in body.seat_type]}

        if body.airline_iata:
            query["airline.iata"] = {"$in": body.airline_iata}

        if body.aircraft_icao:
            query["aircraft.icao"] = {"$in": body.aircraft_icao}

        distance_filter: dict = {}
        if body.distance_gt is not None:
            distance_filter["$gt"] = body.distance_gt
        if body.distance_lt is not None:
            distance_filter["$lt"] = body.distance_lt
        if distance_filter:
            query["distance"] = distance_filter

        if body.from_city:
            query["departure_airport.city"] = {"$in": body.from_city}
        if body.from_country:
            query["departure_airport.country"] = {"$in": body.from_country}
        if body.from_airport_iata:
            query["departure_airport.iata"] = {"$in": body.from_airport_iata}

        if body.to_city:
            query["arrival_airport.city"] = {"$in": body.to_city}
        if body.to_country:
            query["arrival_airport.country"] = {"$in": body.to_country}
        if body.to_airport_iata:
            query["arrival_airport.iata"] = {"$in": body.to_airport_iata}

        and_clauses: list[dict] = []
        if body.city:
            and_clauses.append({"$or": [
                {"departure_airport.city": {"$in": body.city}},
                {"arrival_airport.city": {"$in": body.city}},
            ]})
        if body.country:
            and_clauses.append({"$or": [
                {"departure_airport.country": {"$in": body.country}},
                {"arrival_airport.country": {"$in": body.country}},
            ]})
        if body.airport_iata:
            and_clauses.append({"$or": [
                {"departure_airport.iata": {"$in": body.airport_iata}},
                {"arrival_airport.iata": {"$in": body.airport_iata}},
            ]})
        if and_clauses:
            query["$and"] = and_clauses

        data = await collection.find(query).to_list(length=None)
        if not data:
            return ListResponse(entities=[])

        entities = [to_flight(item) for item in data]
        return ListResponse(entities=entities)

    except Exception as e:
        logger.error(f"Error querying Flights for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while querying Flights: " + str(e)
        )
