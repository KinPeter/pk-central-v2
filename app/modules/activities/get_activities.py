from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.activities.activities_types import ActivitiesConfig
from app.modules.auth.auth_types import CurrentUser


async def get_activities(request: Request, user: CurrentUser) -> ActivitiesConfig:
    """
    Get the Activities config for the user.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.ACTIVITIES)
        data = await collection.find_one({"user_id": user.id})

        if not data:
            logger.error(f"Activities config not found for user {user.id}")
            raise NotFoundException(resource="Activities config")

        return ActivitiesConfig(
            id=data["id"],
            chores=data["chores"],
            walk_weekly_goal=data["walk_weekly_goal"],
            walk_monthly_goal=data["walk_monthly_goal"],
            cycling_weekly_goal=data["cycling_weekly_goal"],
            cycling_monthly_goal=data["cycling_monthly_goal"],
        )

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving Activities config for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while retrieving the Activities config" + str(e)
        )
