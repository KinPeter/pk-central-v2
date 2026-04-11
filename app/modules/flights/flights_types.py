from enum import Enum
from typing import Annotated
from pydantic import Field
from app.common.constants import SIMPLE_DATE_REGEX_POSSIBLE_PAST, SIMPLE_TIME_REGEX, YEAR_REGEX
from app.common.types import BaseEntity, PkBaseModel


class Airport(PkBaseModel):
    iata: str = Field(..., min_length=3, max_length=3)
    icao: str = Field(..., min_length=4, max_length=4)
    name: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class Aircraft(PkBaseModel):
    icao: str = Field(..., min_length=2, max_length=4)
    name: str = Field(..., min_length=1, max_length=100)


class Airline(PkBaseModel):
    iata: str = Field(..., min_length=2, max_length=2)
    icao: str = Field(..., min_length=3, max_length=3)
    name: str = Field(..., min_length=1, max_length=100)


class SeatType(str, Enum):
    AISLE = "Aisle"
    MIDDLE = "Middle"
    WINDOW = "Window"


class FlightClass(str, Enum):
    ECONOMY = "Economy"
    PREMIUM_ECONOMY = "Premium Economy"
    BUSINESS = "Business"
    FIRST = "First"


class FlightReason(str, Enum):
    LEISURE = "Leisure"
    BUSINESS = "Business"
    CREW = "Crew"


class FlightRequest(PkBaseModel):
    flight_number: str = Field(..., min_length=3, max_length=7)
    date: str = Field(..., pattern=SIMPLE_DATE_REGEX_POSSIBLE_PAST)
    departure_airport: Airport
    arrival_airport: Airport
    departure_time: str = Field(..., pattern=SIMPLE_TIME_REGEX)
    arrival_time: str = Field(..., pattern=SIMPLE_TIME_REGEX)
    duration: str = Field(..., pattern=SIMPLE_TIME_REGEX)
    distance: float = Field(..., gt=0)
    airline: Airline
    aircraft: Aircraft
    registration: str | None = Field(default=None, min_length=3, max_length=10)
    seat_number: str | None = Field(default=None, min_length=1, max_length=3)
    seat_type: SeatType | None = Field(default=SeatType.AISLE)
    flight_class: FlightClass | None = Field(default=FlightClass.ECONOMY)
    flight_reason: FlightReason | None = Field(default=FlightReason.LEISURE)
    note: str | None = Field(default=None, max_length=100)
    is_planned: bool = Field(default=False)


class Flight(BaseEntity, FlightRequest):
    pass


class FlightQuery(PkBaseModel):
    year: list[Annotated[str, Field(pattern=YEAR_REGEX)]] | None = None
    is_planned: bool | None = None
    flight_class: list[FlightClass] | None = None
    flight_reason: list[FlightReason] | None = None
    seat_type: list[SeatType] | None = None
    airline_iata: list[str] | None = None
    aircraft_icao: list[str] | None = None
    distance_gt: float | None = None
    distance_lt: float | None = None
    city: list[str] | None = None
    country: list[str] | None = None
    airport_iata: list[str] | None = None
    to_city: list[str] | None = None
    to_country: list[str] | None = None
    to_airport_iata: list[str] | None = None
    from_city: list[str] | None = None
    from_country: list[str] | None = None
    from_airport_iata: list[str] | None = None
