from typing import Annotated
from pydantic import Field
from app.common.constants import YEAR_REGEX
from app.common.responses import OkResponse
from app.common.types import PkBaseModel
from app.modules.flights.flights_types import Airport, Flight
from app.modules.visits.visits_types import Visit


class Trips(OkResponse):
    flights: list[Flight]
    visits: list[Visit]


class AirportResponse(OkResponse, Airport):
    pass


# ── Request bodies ────────────────────────────────────────────────────────────

class TripsStatsRequest(PkBaseModel):
    year: list[Annotated[str, Field(pattern=YEAR_REGEX)]] | None = None
    flight_ids: list[str] | None = None
    visit_ids: list[str] | None = None


class TripsMapsRequest(PkBaseModel):
    year: list[Annotated[str, Field(pattern=YEAR_REGEX)]] | None = None
    flight_ids: list[str] | None = None
    visit_ids: list[str] | None = None


# ── Stats response shapes ─────────────────────────────────────────────────────

class FlightStats(PkBaseModel):
    total_count: int
    domestic_count: int
    intl_count: int
    total_distance: float
    total_duration_minutes: int
    flight_classes_by_count: list[tuple[str, int]]
    reasons_by_count: list[tuple[str, int]]
    seat_type_by_count: list[tuple[str, int]]
    continents_by_count: list[tuple[str, int]]
    total_countries: int
    countries_by_count: list[tuple[str, int]]
    total_airports: int
    airports_by_count: list[tuple[str, int]]
    total_airlines: int
    airlines_by_count: list[tuple[str, int]]
    airlines_by_distance: list[tuple[str, float]]
    total_aircrafts: int
    aircraft_by_count: list[tuple[str, int]]
    aircraft_by_distance: list[tuple[str, float]]
    total_routes: int
    routes_by_count: list[tuple[str, int]]
    routes_by_distance: list[tuple[str, float]]
    flights_per_year: list[tuple[str, int]]
    distance_per_year: list[tuple[str, float]]
    flights_per_month: list[tuple[str, int]]
    flights_per_weekday: list[tuple[str, int]]
    # helpers
    airports_map: dict[str, str]
    airlines_map: dict[str, str]
    aircraft_map: dict[str, str]
    years: list[str]


class VisitStats(PkBaseModel):
    cities_count: int
    countries_count: int


class TripsStats(OkResponse):
    flights: FlightStats
    visits: VisitStats


# ── Map response shapes ───────────────────────────────────────────────────────

class MapMarker(PkBaseModel):
    pos: tuple[float, float]
    popup: str


class FlightMapRoute(PkBaseModel):
    a: tuple[float, float]
    b: tuple[float, float]
    count: int


class FlightMapData(PkBaseModel):
    routes: list[FlightMapRoute]
    markers: list[MapMarker]
    center: tuple[float, float]


class VisitMapData(PkBaseModel):
    markers: list[MapMarker]


class TripsMaps(OkResponse):
    flights: FlightMapData
    visits: VisitMapData
