from pydantic import Field
from app.common.responses import OkResponse


class CityLocation(OkResponse):
    """
    Represents a city location with its name, country, and coordinates.
    """

    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
