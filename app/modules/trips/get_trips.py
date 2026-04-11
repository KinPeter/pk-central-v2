from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException
from app.modules.flights.flights_utils import to_flight
from app.modules.trips.trips_types import Trips
from app.modules.visits.visits_utils import to_visit


async def get_trips(request: Request, user_id: str, year: list[str] | None = None) -> Trips:
    """
    Endpoint to get trips data.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        flights_collection = db.get_collection(DbCollection.FLIGHTS)
        visits_collection = db.get_collection(DbCollection.VISITS)

        flights_query: dict = {"user_id": user_id}
        visits_query: dict = {"user_id": user_id}

        if year:
            year_pattern = "|".join(year)
            flights_query["date"] = {"$regex": f"^({year_pattern})"}
            visits_query["year"] = {"$in": year}

        flights = await flights_collection.find(flights_query).to_list(length=None)
        visits = await visits_collection.find(visits_query).to_list(length=None)

        return Trips(
            flights=[to_flight(flight) for flight in flights],
            visits=[to_visit(visit) for visit in visits],
        )

    except Exception as e:
        logger.error(f"Error getting trips data for user {user_id}: {e}")
        raise InternalServerErrorException("Failed to retrieve trips data: " + str(e))
