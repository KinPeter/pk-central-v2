from typing import Annotated
from pydantic import Field
from app.common.constants import YEAR_REGEX
from app.common.types import BaseEntity, PkBaseModel


class VisitQuery(PkBaseModel):
    year: list[Annotated[str, Field(pattern=YEAR_REGEX)]] | None = None
    country: list[str] | None = None


class VisitRequest(PkBaseModel):
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    year: str | None = Field(None, pattern=YEAR_REGEX)


class Visit(BaseEntity, VisitRequest):
    pass
