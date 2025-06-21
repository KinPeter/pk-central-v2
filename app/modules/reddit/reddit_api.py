import asyncpraw as praw
from logging import Logger

from app.common.environment import PkCentralEnv
from app.modules.reddit.reddit_types import RedditPost
from app.modules.reddit.reddit_utils import parse_post


class RedditApi:
    def __init__(self, env: PkCentralEnv, logger: Logger):
        self.env = env
        self.logger = logger
        self.reddit = self.init_reddit()

    async def fetch_sub_posts(self, sub_name: str, limit: int) -> list[RedditPost]:
        if not self.reddit:
            self.logger.error("Reddit API not initialized")
            raise ValueError("Reddit API not initialized")

        try:
            subreddit = await self.reddit.subreddit(sub_name)
            posts = subreddit.new(limit=limit)
            post_list: list[RedditPost] = []

            async for post in posts:
                post_list.extend(parse_post(submission=post, logger=self.logger))

            return post_list

        except Exception as e:
            self.logger.error(f"Failed to fetch subreddit {sub_name}: {e}")
            return []

    async def fetch_user_posts(self, username: str, limit: int) -> list[RedditPost]:
        if not self.reddit:
            self.logger.error("Reddit API not initialized")
            raise ValueError("Reddit API not initialized")

        try:
            user = await self.reddit.redditor(username)
            posts = user.submissions.new(limit=limit)
            post_list: list[RedditPost] = []

            async for post in posts:
                post_list.extend(parse_post(submission=post, logger=self.logger))

            return post_list

        except Exception as e:
            self.logger.error(f"Failed to fetch posts for user {username}: {e}")
            return []

    def init_reddit(self) -> praw.Reddit | None:
        try:
            reddit = praw.Reddit(
                client_id=self.env.REDDIT_CLIENT_ID,
                client_secret=self.env.REDDIT_CLIENT_SECRET,
                user_agent=self.env.REDDIT_USER_AGENT,
                username=self.env.REDDIT_USER,
                password=self.env.REDDIT_PASSWORD,
            )
            return reddit
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit API: {e}")
            return None

    async def close(self):
        if self.reddit:
            await self.reddit.close()
            self.logger.info("Reddit API connection closed")
        else:
            self.logger.warning("Reddit API was not initialized, nothing to close")
