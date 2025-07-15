from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.activities.activities_types import ActivitiesConfig
from app.modules.auth.auth_types import CurrentUser


async def delete_chore(
    request: Request, id: str, user: CurrentUser
) -> ActivitiesConfig:
    """
    Delete a cycling chore for the current user.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.ACTIVITIES)
        result = await collection.update_one(
            {"user_id": user.id},
            {"$pull": {"chores": {"id": id}}},
        )

        if result.matched_count == 0 or result.modified_count == 0:
            logger.error(
                f"Failed to delete chore {id} for user {user.id}, config not found"
            )
            raise NotFoundException(resource="Chore")

        data = await collection.find_one({"user_id": user.id})

        return ActivitiesConfig(
            id=data["id"],
            walk_weekly_goal=data["walk_weekly_goal"],
            walk_monthly_goal=data["walk_monthly_goal"],
            cycling_weekly_goal=data["cycling_weekly_goal"],
            cycling_monthly_goal=data["cycling_monthly_goal"],
            chores=data["chores"],
        )

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting chore {id} for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while deleting the chore: " + str(e)
        )
