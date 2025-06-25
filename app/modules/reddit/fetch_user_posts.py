import asyncio
from logging import Logger
from random import shuffle
from fastapi import Request
from app.common.db import DbCollection
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, ListResponse
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import CurrentUser
from app.modules.reddit.reddit_api import RedditApi
from app.modules.reddit.reddit_types import RedditPost, RedditUsersRequest


async def fetch_user_posts(
    request: Request, body: RedditUsersRequest, user: CurrentUser
) -> ListResponse[RedditPost]:
    logger: Logger = request.app.state.logger
    env: PkCentralEnv = request.app.state.env
    db: AsyncDatabase = request.app.state.db

    reddit = RedditApi(env, logger)
    if reddit is None:
        raise InternalServerErrorException("Reddit API initialization failed")

    try:
        users = body.usernames if body.usernames else []
        limit = body.limit if body.limit else 10

        logger.info(f"Fetching posts from {len(users)} users with limit: {limit}")

        result: list[RedditPost] = []

        tasks = [reddit.fetch_user_posts(name, limit) for name in users]
        all_posts = await asyncio.gather(*tasks)

        for post_list in all_posts:
            result.extend(post_list)

        if len(users) > 1:
            shuffle(result)

        config_collection = db.get_collection(DbCollection.REDDIT)
        user_config = await config_collection.find_one({"user_id": user.id})

        if user_config and user_config["blocked_users"]:
            result = [
                post
                for post in result
                if post.author not in user_config["blocked_users"]
            ]

        logger.info(f"Fetched {len(result)} images from {len(users)} redditors")
        return ListResponse[RedditPost](entities=result)

    except Exception as e:
        logger.error(f"Failed to fetch user posts: {e}")
        return ListResponse(entities=[])
    finally:
        await reddit.close()
