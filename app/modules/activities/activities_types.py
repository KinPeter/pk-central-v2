from pydantic import Field
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


class ChoreRequest(PkBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    km_interval: int = Field(..., ge=1)
    last_km: float = Field(..., ge=0)


class GoalsRequest(PkBaseModel):
    walk_weekly_goal: int = Field(..., ge=0)
    walk_monthly_goal: int = Field(..., ge=0)
    cycling_weekly_goal: int = Field(..., ge=0)
    cycling_monthly_goal: int = Field(..., ge=0)
