import uuid
import asyncpraw as praw
from datetime import datetime, timezone
from logging import Logger

from app.common.db import DbCollection
from app.common.types import AsyncDatabase
from app.modules.reddit.reddit_types import RedditPost


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


def parse_post(submission: praw.reddit.Submission, logger: Logger) -> list[RedditPost]:
    try:
        posts: list[RedditPost] = []
        if submission.url.endswith((".jpg", "jpeg", ".png", ".gif")):
            posts.append(
                RedditPost(
                    title=submission.title,
                    url=submission.url,
                    author=submission.author.name if submission.author else "Unknown",
                    subreddit=submission.subreddit.display_name,
                )
            )

        elif (
            hasattr(submission, "gallery_data")
            and hasattr(submission, "media_metadata")
            and hasattr(submission.media_metadata, "items")
        ):
            for item in submission.gallery_data["items"]:
                media_id = item["media_id"] if "media_id" in item else None
                if (
                    media_id in submission.media_metadata
                    and "s" in submission.media_metadata[media_id]
                    and "u" in submission.media_metadata[media_id]["s"]
                ):
                    image_url = submission.media_metadata[media_id]["s"]["u"]
                    image_url = image_url.replace("&amp;", "&")
                    posts.append(
                        RedditPost(
                            title=submission.title,
                            url=image_url,
                            author=(
                                submission.author.name
                                if submission.author
                                else "Unknown"
                            ),
                            subreddit=submission.subreddit.display_name,
                        )
                    )

        return posts
    except Exception as e:
        logger.error(f"Failed to parse post: {e}")
        return []
