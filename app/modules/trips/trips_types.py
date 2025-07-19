from app.common.responses import OkResponse
from app.modules.flights.flights_types import Airport, Flight
from app.modules.visits.visits_types import Visit


class Trips(OkResponse):
    flights: list[Flight]
    visits: list[Visit]


class AirportResponse(OkResponse, Airport):
    pass
