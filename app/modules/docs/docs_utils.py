from app.modules.docs.docs_types import Document, DocumentListItem


def to_document_list_item(item: dict) -> DocumentListItem:
    return DocumentListItem(
        id=item["id"],
        title=item["title"],
        tags=item.get("tags", []),
    )


def to_document(item: dict) -> Document:
    return Document(
        id=item["id"],
        title=item["title"],
        tags=item.get("tags", []),
        content=item["content"],
    )
