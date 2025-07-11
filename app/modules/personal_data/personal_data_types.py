from pydantic import Field
from app.common.constants import SIMPLE_DATE_REGEX
from app.common.types import BaseEntity, PkBaseModel


class PersonalDataRequest(PkBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    identifier: str = Field(..., min_length=1, max_length=100)
    expiry: str | None = Field(None, pattern=SIMPLE_DATE_REGEX)


class PersonalData(BaseEntity, PersonalDataRequest):
    pass
