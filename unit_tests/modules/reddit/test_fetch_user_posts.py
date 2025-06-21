import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.reddit.fetch_user_posts import fetch_user_posts
from app.common.responses import ListResponse, InternalServerErrorException
from app.modules.reddit.reddit_types import RedditUsersRequest, RedditPost


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.logger = MagicMock()
    req.app.state.env = MagicMock()
    return req


@pytest.mark.asyncio
async def test_fetch_user_posts_success(mock_request):
    body = RedditUsersRequest(usernames=["user1", "user2"], limit=2)
    posts1 = [MagicMock(spec=RedditPost)]
    posts2 = [MagicMock(spec=RedditPost)]
    with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_user_posts = AsyncMock(side_effect=[posts1, posts2])
        instance.close = AsyncMock()
        result = await fetch_user_posts(mock_request, body)
        assert isinstance(result, ListResponse)
        instance.fetch_user_posts.assert_any_await("user1", 2)
        instance.fetch_user_posts.assert_any_await("user2", 2)
        instance.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_user_posts_empty_usernames(mock_request):
    body = RedditUsersRequest(usernames=[], limit=2)
    with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_user_posts = AsyncMock(return_value=[])
        instance.close = AsyncMock()
        result = await fetch_user_posts(mock_request, body)
        assert isinstance(result, ListResponse)
        assert result.entities == []
        instance.fetch_user_posts.assert_not_awaited()
        instance.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_user_posts_exception(mock_request):
    body = RedditUsersRequest(usernames=["user1"], limit=2)
    with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_user_posts = AsyncMock(side_effect=Exception("fail"))
        instance.close = AsyncMock()
        result = await fetch_user_posts(mock_request, body)
        assert isinstance(result, ListResponse)
        assert result.entities == []
        instance.close.assert_awaited_once()
        mock_request.app.state.logger.error.assert_called()


@pytest.mark.asyncio
async def test_fetch_user_posts_api_init_fail(mock_request):
    body = RedditUsersRequest(usernames=["user1"], limit=2)
    with patch("app.modules.reddit.fetch_user_posts.RedditApi", return_value=None):
        with pytest.raises(InternalServerErrorException):
            await fetch_user_posts(mock_request, body)
