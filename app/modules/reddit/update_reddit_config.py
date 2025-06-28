from ast import Not
from fastapi import Request
from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.auth.auth_types import CurrentUser
from app.modules.reddit.reddit_types import RedditConfig, RedditConfigRequest


async def update_reddit_config(
    request: Request, body: RedditConfigRequest, user: CurrentUser
) -> RedditConfig:
    """
    Update the Reddit configuration for the current user.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.REDDIT)
        result = await collection.update_one(
            {"user_id": user.id},
            {
                "$set": body.model_dump(
                    exclude_none=True, exclude_unset=True, mode="json"
                )
            },
        )

        if result.matched_count == 0:
            logger.error(f"Failed to update Reddit configuration for user {user.id}")
            raise NotFoundException(resource="Reddit configuration")

        updated_config = await collection.find_one({"user_id": user.id})

        return RedditConfig(
            id=updated_config["id"],
            created_at=updated_config["created_at"],
            sets=updated_config["sets"],
            blocked_users=updated_config["blocked_users"],
        )

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating Reddit configuration for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while updating the Reddit configuration" + str(e)
        )
