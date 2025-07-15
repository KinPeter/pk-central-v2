import pytest
from pydantic import HttpUrl
from app.modules.shortcuts.shortcuts_utils import to_shortcut
from app.modules.shortcuts.shortcuts_types import Shortcut, ShortcutCategory


@pytest.mark.parametrize(
    "item,expected",
    [
        # All fields present
        (
            {
                "id": "s1",
                "name": "Test Shortcut",
                "url": "https://example.com",
                "icon_url": "icon.png",
                "category": "CODING",
                "priority": 1,
            },
            Shortcut(
                id="s1",
                name="Test Shortcut",
                url=HttpUrl("https://example.com/"),
                icon_url="icon.png",
                category=ShortcutCategory.CODING,
                priority=1,
            ),
        ),
        # Different values
        (
            {
                "id": "s2",
                "name": "Another Shortcut",
                "url": "https://another.com",
                "icon_url": "icon.png",
                "category": "GOOGLE",
                "priority": 5,
            },
            Shortcut(
                id="s2",
                name="Another Shortcut",
                url=HttpUrl("https://another.com/"),
                icon_url="icon.png",
                category=ShortcutCategory.GOOGLE,
                priority=5,
            ),
        ),
    ],
)
def test_to_shortcut(item, expected):
    shortcut = to_shortcut(item)
    assert isinstance(shortcut, Shortcut)
    assert shortcut.id == expected.id
    assert shortcut.name == expected.name
    assert str(shortcut.url) == str(expected.url)
    assert str(shortcut.icon_url) == str(expected.icon_url)
    assert shortcut.category == expected.category
    assert shortcut.priority == expected.priority
