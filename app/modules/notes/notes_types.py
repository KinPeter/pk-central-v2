from pydantic import Field, HttpUrl
from app.common.responses import OkResponse
from app.common.types import BaseEntity, PkBaseModel


class Link(PkBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl


class NoteRequest(PkBaseModel):
    text: str | None = Field(None, max_length=1000)
    links: list[Link] = Field(default_factory=list)
    archived: bool = False
    pinned: bool = False


class Note(BaseEntity, NoteRequest):
    pass
