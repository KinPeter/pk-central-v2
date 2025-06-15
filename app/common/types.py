from pydantic import BaseModel, ConfigDict
from pymongo.asynchronous.database import AsyncDatabase as AsyncMongoDatabase

AsyncDatabase = AsyncMongoDatabase


def to_camel(string: str) -> str:
    """Convert a snake_case string to camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class PkBaseModel(BaseModel):
    """
    Base model extending Pydantic's BaseModel with a custom configuration.
    This model uses a custom alias generator to convert field names from snake_case to camelCase.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
