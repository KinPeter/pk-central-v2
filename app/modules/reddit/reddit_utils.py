from datetime import datetime, timezone
from logging import Logger
import uuid
from app.common.db import DbCollection
from app.common.types import AsyncDatabase


async def create_initial_reddit_config(
    db: AsyncDatabase, logger: Logger, user_id: str
) -> None:
    """
    Create initial Reddit configuration for a new user.
    This includes favorite subreddits and usernames.
    """
    default_config = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc),
        "user_id": user_id,
        "sets": [
            {
                "name": "Default",
                "subs": [],
                "usernames": [],
            }
        ],
        "blocked_users": [],
    }

    collection = db.get_collection(DbCollection.REDDIT)
    existing_config = await collection.find_one({"user_id": user_id})
    if existing_config:
        logger.warning(f"Reddit config already exists for user {user_id}")
        raise ValueError(f"Reddit config already exists for user {user_id}")

    await collection.insert_one(default_config)

    logger.info(f"Initial Reddit config created for user {user_id}")
