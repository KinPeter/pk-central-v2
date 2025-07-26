from enum import Enum

from app.common.responses import OkResponse
from app.common.types import PkBaseModel


class StravaDbCollection(str, Enum):
    """
    Enum for Strava database collections.
    """

    ACTIVITIES = "activities"
    SYNC_META = "sync_metadata"


class StravaActivityType(str, Enum):
    WALK = "Walk"
    RUN = "Run"
    RIDE = "Ride"


class StravaSyncResponse(OkResponse):
    routes_synced: int
    total_routes: int


Coords = tuple[float, float]  # (latitude, longitude)


class StravaRoutemap(PkBaseModel):
    count: int = 0
    points: set[Coords] = set()


class StravaRoutesResponse(OkResponse):
    routemap: StravaRoutemap | None = None
    after: str | None = None
    before: str | None = None
    types: list[StravaActivityType]
    activity_count: int
