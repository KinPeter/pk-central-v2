import asyncio
from random import shuffle
from fastapi import Request
from app.common.responses import InternalServerErrorException, ListResponse
from app.modules.reddit.reddit_api import RedditApi
from app.modules.reddit.reddit_types import RedditPost, RedditSubsRequest


async def fetch_sub_posts(
    request: Request, body: RedditSubsRequest
) -> ListResponse[RedditPost]:
    logger = request.app.state.logger
    env = request.app.state.env

    reddit = RedditApi(env, logger)
    if reddit is None:
        raise InternalServerErrorException("Reddit API initialization failed")

    try:
        subs = body.subs if body.subs else []
        limit = body.limit if body.limit else 10

        logger.info(f"Fetching posts from {len(subs)} subreddits with limit: {limit}")

        result: list[RedditPost] = []

        tasks = [reddit.fetch_sub_posts(sub_name, limit) for sub_name in subs]
        all_posts = await asyncio.gather(*tasks)

        for post_list in all_posts:
            result.extend(post_list)

        if len(subs) > 1:
            shuffle(result)

        logger.info(f"Fetched {len(result)} images from {len(subs)} subreddits")
        return ListResponse[RedditPost](entities=result)

    except Exception as e:
        logger.error(f"Failed to fetch sub posts: {e}")
        return ListResponse(entities=[])
    finally:
        await reddit.close()
