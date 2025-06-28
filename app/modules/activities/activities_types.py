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
