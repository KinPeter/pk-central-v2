from app.modules.visits.visits_types import Visit


def to_visit(item: dict) -> Visit:
    return Visit(
        id=item["id"],
        created_at=item["created_at"],
        city=item["city"],
        country=item["country"],
        lat=item["lat"],
        lng=item["lng"],
        year=item.get("year"),
    )
