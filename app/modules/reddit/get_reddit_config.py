from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.auth.auth_types import CurrentUser
from app.modules.reddit.reddit_types import RedditConfig


async def get_reddit_config(request: Request, user: CurrentUser) -> RedditConfig:
    """
    Get the Reddit configuration for the current user.
    This includes favorite subreddits and usernames.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.REDDIT)
        config = await collection.find_one({"user_id": user.id})

        if not config:
            logger.error(f"Reddit configuration not found for user {user.id}")
            raise NotFoundException(resource="Reddit configuration")

        return RedditConfig(
            id=config["id"],
            sets=config["sets"],
            blocked_users=config["blocked_users"],
        )

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving Reddit configuration for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while retrieving the Reddit configuration" + str(e)
        )
