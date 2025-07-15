import pytest
from pydantic import HttpUrl
from app.modules.notes.notes_utils import to_note
from app.modules.notes.notes_types import Note, Link
from datetime import datetime, timezone


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "item,expected",
    [
        # All fields present, multiple links
        (
            {
                "id": "n1",
                "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
                "text": "Test note",
                "links": [
                    {"name": "Google", "url": "https://google.com"},
                    {"name": "GitHub", "url": "https://github.com"},
                    {"name": "Python", "url": "https://python.org"},
                ],
                "archived": True,
                "pinned": True,
            },
            {
                "id": "n1",
                "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
                "text": "Test note",
                "links": [
                    Link(name="Google", url=HttpUrl("https://google.com")),
                    Link(name="GitHub", url=HttpUrl("https://github.com")),
                    Link(name="Python", url=HttpUrl("https://python.org")),
                ],
                "archived": True,
                "pinned": True,
            },
        ),
        # Only required fields
        (
            {
                "id": "n2",
                "created_at": datetime(2024, 1, 2, tzinfo=timezone.utc).isoformat(),
            },
            {
                "id": "n2",
                "created_at": datetime(2024, 1, 2, tzinfo=timezone.utc).isoformat(),
                "text": None,
                "links": [],
                "archived": False,
                "pinned": False,
            },
        ),
        # Some fields missing
        (
            {
                "id": "n3",
                "created_at": datetime(2024, 1, 3, tzinfo=timezone.utc).isoformat(),
                "text": None,
                "links": [],
            },
            {
                "id": "n3",
                "created_at": datetime(2024, 1, 3, tzinfo=timezone.utc).isoformat(),
                "text": None,
                "links": [],
                "archived": False,
                "pinned": False,
            },
        ),
    ],
)
async def test_to_note(item, expected):
    note = to_note(item)
    assert isinstance(note, Note)
    assert note.id == expected["id"]
    assert note.created_at == expected["created_at"]
    assert note.text == expected["text"]
    assert note.archived == expected["archived"]
    assert note.pinned == expected["pinned"]
    # Compare links as list of dicts for easier equality
    assert [l.model_dump() for l in note.links] == [
        l.model_dump() for l in expected["links"]
    ]
