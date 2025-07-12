from app.modules.birthdays.birthdays_types import Birthday


def to_birthday(data: dict) -> Birthday:
    return Birthday(
        id=data["id"],
        created_at=data["created_at"],
        name=data["name"],
        date=data["date"],
    )
