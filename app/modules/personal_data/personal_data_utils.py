from app.modules.personal_data.personal_data_types import PersonalData


def to_personal_data(item: dict) -> PersonalData:
    return PersonalData(
        id=item["id"],
        name=item["name"],
        identifier=item["identifier"],
        expiry=item.get("expiry"),
    )
