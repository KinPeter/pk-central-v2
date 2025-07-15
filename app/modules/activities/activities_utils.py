from logging import Logger
import uuid
from app.common.db import DbCollection
from app.common.types import AsyncDatabase


async def create_initial_activities_config(
    db: AsyncDatabase,
    logger: Logger,
    user_id: str,
):
    """
    Create an initial Activities config config for the user.
    """
    collection = db.get_collection(DbCollection.ACTIVITIES)

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "chores": [],
        "walk_weekly_goal": 0,
        "walk_monthly_goal": 0,
        "cycling_weekly_goal": 0,
        "cycling_monthly_goal": 0,
    }

    collection = db.get_collection(DbCollection.ACTIVITIES)
    existing_config = await collection.find_one({"user_id": user_id})
    if existing_config:
        logger.warning(f"Activities config already exists for user {user_id}")
        raise ValueError(f"Activities config already exists for user {user_id}")

    await collection.insert_one(data)

    logger.info(f"Initial Activities config created for user {user_id}")
