from datetime import datetime, timezone
from logging import Logger
import uuid
from app.common.db import DbCollection
from app.common.types import AsyncDatabase


async def create_initial_settings(
    db: AsyncDatabase,
    logger: Logger,
    user_id: str,
):
    """
    Create an initial Start Settings config for the user.
    """
    collection = db.get_collection(DbCollection.START_SETTINGS)

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "name": None,
        "shortcut_icon_base_url": None,
        "strava_redirect_uri": None,
    }

    collection = db.get_collection(DbCollection.START_SETTINGS)
    existing_config = await collection.find_one({"user_id": user_id})
    if existing_config:
        logger.warning(f"Start settings already exists for user {user_id}")
        raise ValueError(f"Start settings already exists for user {user_id}")

    await collection.insert_one(data)

    logger.info(f"Initial start settings created for user {user_id}")
