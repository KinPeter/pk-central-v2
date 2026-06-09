from datetime import datetime, timedelta, timezone

from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.activities.activities_types import ActivitiesStats, ActivityStats
from app.modules.activities.activities_utils import sum_distance, sum_steps
from app.modules.auth.auth_types import CurrentUser


async def get_stats(request: Request, user: CurrentUser) -> ActivitiesStats:
    """
    Compute aggregated activity stats (walk, cycling, steps) for the current
    and previous week/month, combined with the user's goals, chores and bike kms.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        today = datetime.now(timezone.utc)
        today_str = today.strftime("%Y-%m-%d")

        # --- 1. Fetch activities config (goals + chores) ---
        config_collection = db.get_collection(DbCollection.ACTIVITIES_CONFIG)
        config_data = await config_collection.find_one({"user_id": user.id})

        if not config_data:
            logger.error(f"Activities config not found for user {user.id}")
            raise NotFoundException(resource="Activities config")

        # --- 2. Fetch current_bike_kms ---
        sync_meta_collection = db.get_collection(DbCollection.ACTIVITIES_SYNC_META)
        sync_meta = await sync_meta_collection.find_one({"user_id": user.id})

        if not sync_meta:
            logger.error(f"Activities sync meta not found for user {user.id}")
            raise NotFoundException(resource="Activities sync meta")

        # --- 3. Compute date boundaries ---
        monday = today - timedelta(days=today.weekday())  # Monday of this week
        this_week_start = monday.strftime("%Y-%m-%d")

        last_week_end_dt = monday - timedelta(days=1)  # Sunday of last week
        last_week_start = (last_week_end_dt - timedelta(days=6)).strftime("%Y-%m-%d")
        last_week_end = last_week_end_dt.strftime("%Y-%m-%d")

        this_month_start = today.replace(day=1).strftime("%Y-%m-%d")

        first_of_this_month = today.replace(day=1)
        last_month_end_dt = first_of_this_month - timedelta(days=1)
        last_month_start = last_month_end_dt.replace(day=1).strftime("%Y-%m-%d")
        last_month_end = last_month_end_dt.strftime("%Y-%m-%d")

        # --- 4. Query activities for distances ---
        activities_collection = db.get_collection(DbCollection.ACTIVITIES)

        walk = ActivityStats(
            this_week=await sum_distance(
                activities_collection, user.id, "walk", this_week_start, today_str
            ),
            last_week=await sum_distance(
                activities_collection, user.id, "walk", last_week_start, last_week_end
            ),
            this_month=await sum_distance(
                activities_collection, user.id, "walk", this_month_start, today_str
            ),
            last_month=await sum_distance(
                activities_collection, user.id, "walk", last_month_start, last_month_end
            ),
        )

        cycling = ActivityStats(
            this_week=await sum_distance(
                activities_collection, user.id, "ride", this_week_start, today_str
            ),
            last_week=await sum_distance(
                activities_collection, user.id, "ride", last_week_start, last_week_end
            ),
            this_month=await sum_distance(
                activities_collection, user.id, "ride", this_month_start, today_str
            ),
            last_month=await sum_distance(
                activities_collection, user.id, "ride", last_month_start, last_month_end
            ),
        )

        # --- 5. Query steps ---
        steps_collection = db.get_collection(DbCollection.STEPS)

        steps = ActivityStats(
            this_week=await sum_steps(
                steps_collection, user.id, this_week_start, today_str
            ),
            last_week=await sum_steps(
                steps_collection, user.id, last_week_start, last_week_end
            ),
            this_month=await sum_steps(
                steps_collection, user.id, this_month_start, today_str
            ),
            last_month=await sum_steps(
                steps_collection, user.id, last_month_start, last_month_end
            ),
        )

        # --- 6. Build response ---
        return ActivitiesStats(
            id=config_data["id"],
            chores=config_data.get("chores", []),
            walk_weekly_goal=config_data.get("walk_weekly_goal", 0),
            walk_monthly_goal=config_data.get("walk_monthly_goal", 0),
            cycling_weekly_goal=config_data.get("cycling_weekly_goal", 0),
            cycling_monthly_goal=config_data.get("cycling_monthly_goal", 0),
            steps_weekly_goal=config_data.get("steps_weekly_goal", 0),
            steps_monthly_goal=config_data.get("steps_monthly_goal", 0),
            walk=walk,
            cycling=cycling,
            steps=steps,
            current_bike_kms=round(float(sync_meta.get("current_bike_kms", 0)), 1),
        )

    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error computing activities stats for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while computing activities stats: " + str(e)
        )
