import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.reddit.reddit_api import RedditApi


@pytest.fixture(autouse=True)
def patch_praw_reddit():
    with patch("app.modules.reddit.reddit_api.praw.Reddit") as mock_reddit:
        yield mock_reddit


@pytest.fixture
def env():
    mock_env = MagicMock()
    mock_env.REDDIT_CLIENT_ID = "id"
    mock_env.REDDIT_CLIENT_SECRET = "secret"
    mock_env.REDDIT_USER_AGENT = "agent"
    mock_env.REDDIT_USER = "user"
    mock_env.REDDIT_PASSWORD = "pass"
    return mock_env


@pytest.fixture
def logger():
    return MagicMock()


@pytest.mark.asyncio
async def test_fetch_sub_posts_api_not_initialized(env, logger):
    api = RedditApi(env, logger)
    api.reddit = None
    with pytest.raises(ValueError):
        await api.fetch_sub_posts("testsub", 1)
    logger.error.assert_called_with("Reddit API not initialized")


@pytest.mark.asyncio
async def test_fetch_sub_posts_exception(env, logger):
    api = RedditApi(env, logger)
    api.reddit = MagicMock()
    api.reddit.subreddit = AsyncMock(side_effect=Exception("fail"))
    result = await api.fetch_sub_posts("testsub", 1)
    assert result == []
    logger.error.assert_any_call("Failed to fetch subreddit testsub: fail")


@pytest.mark.asyncio
async def test_fetch_user_posts_api_not_initialized(env, logger):
    api = RedditApi(env, logger)
    api.reddit = None
    with pytest.raises(ValueError):
        await api.fetch_user_posts("testuser", 1)
    logger.error.assert_called_with("Reddit API not initialized")


@pytest.mark.asyncio
async def test_fetch_user_posts_exception(env, logger):
    api = RedditApi(env, logger)
    api.reddit = MagicMock()
    api.reddit.redditor = AsyncMock(side_effect=Exception("fail"))
    result = await api.fetch_user_posts("testuser", 1)
    assert result == []
    logger.error.assert_any_call("Failed to fetch posts for user testuser: fail")


def test_init_reddit_success(env, logger):
    with patch("app.modules.reddit.reddit_api.praw.Reddit") as mock_reddit:
        api = RedditApi(env, logger)
        reddit_instance = mock_reddit.return_value
        assert api.init_reddit() == reddit_instance


def test_init_reddit_failure(env, logger):
    with patch(
        "app.modules.reddit.reddit_api.praw.Reddit", side_effect=Exception("fail")
    ):
        api = RedditApi(env, logger)
        assert api.init_reddit() is None
        logger.error.assert_any_call("Failed to initialize Reddit API: fail")


@pytest.mark.asyncio
async def test_close_success(env, logger):
    api = RedditApi(env, logger)
    api.reddit = AsyncMock()
    await api.close()
    api.reddit.close.assert_awaited_once()
    logger.info.assert_called_with("Reddit API connection closed")


@pytest.mark.asyncio
async def test_close_not_initialized(env, logger):
    api = RedditApi(env, logger)
    api.reddit = None
    await api.close()
    logger.warning.assert_called_with(
        "Reddit API was not initialized, nothing to close"
    )


@pytest.mark.asyncio
def make_async_iter(items):
    class AsyncIter:
        def __init__(self, items):
            self._items = list(items)

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self._items:
                raise StopAsyncIteration
            return self._items.pop(0)

    return AsyncIter(items)


@pytest.mark.asyncio
async def test_fetch_user_posts_success(env, logger):
    api = RedditApi(env, logger)
    api.reddit = MagicMock()
    redditor = AsyncMock()
    post = MagicMock()
    with patch("app.modules.reddit.reddit_api.parse_post", return_value=["parsed"]):
        api.reddit.redditor = AsyncMock(return_value=redditor)
        submissions_mock = MagicMock()
        submissions_mock.new.return_value = make_async_iter([post])
        redditor.submissions = submissions_mock
        result = await api.fetch_user_posts("testuser", 1)
        assert result == ["parsed"]


@pytest.mark.asyncio
async def test_fetch_sub_posts_success(env, logger):
    api = RedditApi(env, logger)
    api.reddit = MagicMock()
    subreddit = MagicMock()
    post = MagicMock()
    with patch("app.modules.reddit.reddit_api.parse_post", return_value=["parsed"]):
        # Make subreddit.new(limit=...) return an object with __aiter__ returning [post]
        async def async_iter():
            yield post

        subreddit.new.return_value = async_iter()
        api.reddit.subreddit = AsyncMock(return_value=subreddit)
        result = await api.fetch_sub_posts("testsub", 1)
        assert result == ["parsed"]
