from app.modules.shortcuts.shortcuts_types import Shortcut


def to_shortcut(item: dict) -> Shortcut:
    return Shortcut(
        id=item["id"],
        created_at=item["created_at"],
        name=item["name"],
        url=item["url"],
        icon_url=item["icon_url"],
        category=item["category"],
        priority=item["priority"],
    )
