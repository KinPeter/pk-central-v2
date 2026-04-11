from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException
from app.modules.flights.flights_utils import to_flight
from app.modules.trips.trips_utils import compute_flights_map, compute_visits_map
from app.modules.trips.trips_types import TripsMaps, TripsMapsRequest
from app.modules.visits.visits_utils import to_visit


async def get_trips_maps(request: Request, user_id: str, body: TripsMapsRequest) -> TripsMaps:
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        flights_collection = db.get_collection(DbCollection.FLIGHTS)
        visits_collection = db.get_collection(DbCollection.VISITS)

        flights_query: dict = {"user_id": user_id, "is_planned": False}
        if body.year:
            flights_query["date"] = {"$regex": f"^({'|'.join(body.year)})"}
        elif body.flight_ids is not None:
            flights_query["id"] = {"$in": body.flight_ids}
        raw_flights = await flights_collection.find(flights_query).to_list(length=None)

        visits_query: dict = {"user_id": user_id}
        if body.year:
            visits_query["year"] = {"$in": body.year}
        elif body.visit_ids is not None:
            visits_query["id"] = {"$in": body.visit_ids}
        raw_visits = await visits_collection.find(visits_query).to_list(length=None)

        flights = [to_flight(f) for f in raw_flights]
        visits = [to_visit(v) for v in raw_visits]

        return TripsMaps(
            flights=compute_flights_map(flights),
            visits=compute_visits_map(visits),
        )

    except Exception as e:
        logger.error(f"Error computing trips maps for user {user_id}: {e}")
        raise InternalServerErrorException("Failed to compute trips maps: " + str(e))
