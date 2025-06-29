import uuid
from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.activities.activities_types import ActivitiesConfig, ChoreRequest
from app.modules.auth.auth_types import CurrentUser


async def add_chore(
    request: Request, body: ChoreRequest, user: CurrentUser
) -> ActivitiesConfig:
    """
    Add a new cycling chore for the current user.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.ACTIVITIES)
        chore_data = body.model_dump(exclude_none=True, exclude_unset=True, mode="json")
        chore_data["id"] = str(uuid.uuid4())

        result = await collection.update_one(
            {"user_id": user.id},
            {"$push": {"chores": chore_data}},
        )

        if result.matched_count == 0:
            logger.error(f"Failed to add chore for user {user.id}, config not found")
            raise NotFoundException(resource="Chore")

        data = await collection.find_one({"user_id": user.id})

        return ActivitiesConfig(
            id=data["id"],
            created_at=data["created_at"],
            walk_weekly_goal=data["walk_weekly_goal"],
            walk_monthly_goal=data["walk_monthly_goal"],
            cycling_weekly_goal=data["cycling_weekly_goal"],
            cycling_monthly_goal=data["cycling_monthly_goal"],
            chores=data["chores"],
        )

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Error adding chore for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while adding the chore: " + str(e)
        )
