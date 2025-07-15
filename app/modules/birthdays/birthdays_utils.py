from app.modules.birthdays.birthdays_types import Birthday


def to_birthday(data: dict) -> Birthday:
    return Birthday(
        id=data["id"],
        name=data["name"],
        date=data["date"],
    )
