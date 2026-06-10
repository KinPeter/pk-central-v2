from enum import Enum

from pydantic import Field
from app.common.constants import SIMPLE_DATE_REGEX
from app.common.responses import OkResponse
from app.common.types import BaseEntity, PkBaseModel


class CyclingChore(PkBaseModel):
    id: str
    name: str
    km_interval: int
    last_km: float


class ActivitiesConfig(OkResponse, BaseEntity):
    chores: list[CyclingChore]
    walk_weekly_goal: int
    walk_monthly_goal: int
    cycling_weekly_goal: int
    cycling_monthly_goal: int
    steps_weekly_goal: int
    steps_monthly_goal: int


class ActivityStats(PkBaseModel):
    this_week: float
    last_week: float
    this_month: float
    last_month: float


class ActivitiesStats(ActivitiesConfig):
    walk: ActivityStats
    cycling: ActivityStats
    steps: ActivityStats
    current_bike_kms: float


class ChoreRequest(PkBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    km_interval: int = Field(..., ge=1)
    last_km: float = Field(..., ge=0)


class GoalsRequest(PkBaseModel):
    walk_weekly_goal: int = Field(..., ge=0)
    walk_monthly_goal: int = Field(..., ge=0)
    cycling_weekly_goal: int = Field(..., ge=0)
    cycling_monthly_goal: int = Field(..., ge=0)
    steps_weekly_goal: int = Field(0, ge=0)
    steps_monthly_goal: int = Field(0, ge=0)


class StepsItem(PkBaseModel):
    steps: int
    date: str


class StepsSyncResponse(OkResponse):
    days_synced: int
    total_days: int


class VerifyActivitySyncRequest(PkBaseModel):
    activity_ids: list[str] = Field(default_factory=list)


class VerifyActivitySyncResponse(OkResponse):
    unsynced: list[str] = Field(default_factory=list)


class ActivityType(str, Enum):
    WALK = "walk"
    RIDE = "ride"
    BOATING = "boating"


class ActivityData(PkBaseModel):
    type: ActivityType
    source_id: str
    name: str
    start_date: str
    moving_time: int  # sec
    elapsed_time: int  # sec
    distance: float  # meters
    total_elevation_gain: float  # meters
    average_speed: float  # m/s
    max_speed: float  # m/s
    average_heartrate: float | None  # bpm
    max_heartrate: float | None  # bpm
    average_cadence: float | None  # rpm
    max_cadence: float | None  # rpm


class Activity(BaseEntity, ActivityData):
    pass


class ActivityQuery(PkBaseModel):
    types: list[ActivityType] = Field(default_factory=list)
    from_date: str | None = Field(default=None, pattern=SIMPLE_DATE_REGEX)
    to_date: str | None = Field(default=None, pattern=SIMPLE_DATE_REGEX)
