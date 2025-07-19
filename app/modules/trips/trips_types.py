from app.common.responses import OkResponse
from app.modules.flights.flights_types import Airport


class AirportResponse(OkResponse, Airport):
    pass
