from app.modules.notes.notes_types import Note


def to_note(item: dict) -> Note:
    return Note(
        id=item["id"],
        created_at=item["created_at"],
        text=item.get("text"),
        links=item.get("links", []),
        archived=item.get("archived", False),
        pinned=item.get("pinned", False),
    )
