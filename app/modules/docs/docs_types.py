from typing import Annotated, List
from pydantic import Field, StringConstraints
from app.common.responses import OkResponse
from app.common.types import BaseEntity, PkBaseModel


class DocumentMeta(PkBaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    tags: List[Annotated[str, StringConstraints(min_length=1, max_length=16)]] = Field(
        default_factory=list
    )


class DocumentRequest(DocumentMeta):
    content: str = Field(..., min_length=1)


class DocumentListItem(BaseEntity, DocumentMeta):
    pass


class Document(OkResponse, BaseEntity, DocumentRequest):
    pass


docs_list_item_projection = {
    "content": 0,
}
