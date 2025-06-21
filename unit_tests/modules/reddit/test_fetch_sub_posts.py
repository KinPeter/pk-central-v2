import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.reddit.fetch_sub_posts import fetch_sub_posts
from app.common.responses import ListResponse, InternalServerErrorException
from app.modules.reddit.reddit_types import RedditSubsRequest, RedditPost


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.logger = MagicMock()
    req.app.state.env = MagicMock()
    return req


@pytest.mark.asyncio
async def test_fetch_sub_posts_success(mock_request):
    body = RedditSubsRequest(subs=["sub1", "sub2"], limit=2)
    posts1 = [MagicMock(spec=RedditPost)]
    posts2 = [MagicMock(spec=RedditPost)]
    with patch("app.modules.reddit.fetch_sub_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_sub_posts = AsyncMock(side_effect=[posts1, posts2])
        instance.close = AsyncMock()
        result = await fetch_sub_posts(mock_request, body)
        assert isinstance(result, ListResponse)
        assert set(result.entities) == set(posts1 + posts2)
        instance.fetch_sub_posts.assert_any_await("sub1", 2)
        instance.fetch_sub_posts.assert_any_await("sub2", 2)
        instance.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_sub_posts_empty_subs(mock_request):
    body = RedditSubsRequest(subs=[], limit=2)
    with patch("app.modules.reddit.fetch_sub_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_sub_posts = AsyncMock(return_value=[])
        instance.close = AsyncMock()
        result = await fetch_sub_posts(mock_request, body)
        assert isinstance(result, ListResponse)
        assert result.entities == []
        instance.fetch_sub_posts.assert_not_awaited()
        instance.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_sub_posts_exception(mock_request):
    body = RedditSubsRequest(subs=["sub1"], limit=2)
    with patch("app.modules.reddit.fetch_sub_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_sub_posts = AsyncMock(side_effect=Exception("fail"))
        instance.close = AsyncMock()
        result = await fetch_sub_posts(mock_request, body)
        assert isinstance(result, ListResponse)
        assert result.entities == []
        instance.close.assert_awaited_once()
        mock_request.app.state.logger.error.assert_called()


@pytest.mark.asyncio
async def test_fetch_sub_posts_api_init_fail(mock_request):
    body = RedditSubsRequest(subs=["sub1"], limit=2)
    with patch("app.modules.reddit.fetch_sub_posts.RedditApi", return_value=None):
        with pytest.raises(InternalServerErrorException):
            await fetch_sub_posts(mock_request, body)
