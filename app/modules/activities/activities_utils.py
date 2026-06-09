from logging import Logger
import uuid
from app.common.db import DbCollection
from app.common.date_utils import to_iso_day_start, to_iso_day_end
from app.common.types import AsyncDatabase


async def sum_distance(
    collection, user_id: str, activity_type: str, start_bound: str, end_bound: str
) -> float:
    """Sum activity distances in kilometers for a given type and date range."""
    cursor = collection.find(
        {
            "user_id": user_id,
            "type": activity_type,
            "start_date": {
                "$gte": to_iso_day_start(start_bound),
                "$lte": to_iso_day_end(end_bound),
            },
        }
    )
    docs = await cursor.to_list(length=None)
    total_meters = sum(d.get("distance", 0) for d in docs)
    return round(total_meters / 1000, 1)


async def sum_steps(
    collection, user_id: str, start_bound: str, end_bound: str
) -> float:
    """Sum steps for a given date range. Steps dates are stored as YYYY-MM-DD."""
    cursor = collection.find(
        {
            "user_id": user_id,
            "date": {"$gte": start_bound, "$lte": end_bound},
        }
    )
    docs = await cursor.to_list(length=None)
    return float(sum(d.get("steps", 0) for d in docs))


async def create_initial_activities_config(
    db: AsyncDatabase,
    logger: Logger,
    user_id: str,
):
    """
    Create an initial Activities config config for the user.
    """
    collection = db.get_collection(DbCollection.ACTIVITIES_CONFIG)

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "chores": [],
        "walk_weekly_goal": 0,
        "walk_monthly_goal": 0,
        "cycling_weekly_goal": 0,
        "cycling_monthly_goal": 0,
        "steps_weekly_goal": 0,
        "steps_monthly_goal": 0,
    }

    collection = db.get_collection(DbCollection.ACTIVITIES_CONFIG)
    existing_config = await collection.find_one({"user_id": user_id})
    if existing_config:
        logger.warning(f"Activities config already exists for user {user_id}")
        raise ValueError(f"Activities config already exists for user {user_id}")

    await collection.insert_one(data)

    logger.info(f"Initial Activities config created for user {user_id}")
