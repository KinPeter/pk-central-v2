from pydantic import Field
from app.common.constants import MONTH_PER_DAY_REGEX
from app.common.types import BaseEntity, PkBaseModel


class BirthdayRequest(PkBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., pattern=MONTH_PER_DAY_REGEX)


class Birthday(BaseEntity, BirthdayRequest):
    pass
