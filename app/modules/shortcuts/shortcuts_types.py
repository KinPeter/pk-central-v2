from enum import Enum

from pydantic import Field, HttpUrl
from app.common.types import BaseEntity, PkBaseModel


class ShortcutCategory(str, Enum):
    TOP = "TOP"
    CODING = "CODING"
    GOOGLE = "GOOGLE"
    HOBBIES = "HOBBIES"
    FUN = "FUN"
    OTHERS = "OTHERS"


class ShortcutRequest(PkBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    icon_url: HttpUrl
    category: ShortcutCategory
    priority: int = Field(..., ge=1, le=10)


class Shortcut(BaseEntity, ShortcutRequest):
    pass
