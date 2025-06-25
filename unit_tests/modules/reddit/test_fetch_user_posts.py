import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.reddit.fetch_user_posts import fetch_user_posts
from app.common.responses import ListResponse, InternalServerErrorException
from app.modules.reddit.reddit_types import RedditUsersRequest, RedditPost
from app.modules.auth.auth_types import CurrentUser


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.logger = MagicMock()
    req.app.state.env = MagicMock()
    req.app.state.db = MagicMock()
    return req


@pytest.fixture
def mock_user():
    user = MagicMock(spec=CurrentUser)
    user.id = "user123"
    return user


@pytest.mark.asyncio
async def test_fetch_user_posts_success(mock_request, mock_user):
    body = RedditUsersRequest(usernames=["user1", "user2"], limit=2)
    posts1 = [MagicMock(spec=RedditPost)]
    posts2 = [MagicMock(spec=RedditPost)]
    with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_user_posts = AsyncMock(side_effect=[posts1, posts2])
        instance.close = AsyncMock()
        # Mock DB config
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_request.app.state.db.get_collection.return_value = mock_collection
        result = await fetch_user_posts(mock_request, body, mock_user)
        assert isinstance(result, ListResponse)
        instance.fetch_user_posts.assert_any_await("user1", 2)
        instance.fetch_user_posts.assert_any_await("user2", 2)
        instance.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_user_posts_empty_usernames(mock_request, mock_user):
    body = RedditUsersRequest(usernames=[], limit=2)
    with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_user_posts = AsyncMock(return_value=[])
        instance.close = AsyncMock()
        # Mock DB config
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_request.app.state.db.get_collection.return_value = mock_collection
        result = await fetch_user_posts(mock_request, body, mock_user)
        assert isinstance(result, ListResponse)
        assert result.entities == []
        instance.fetch_user_posts.assert_not_awaited()
        instance.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_user_posts_exception(mock_request, mock_user):
    body = RedditUsersRequest(usernames=["user1"], limit=2)
    with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_user_posts = AsyncMock(side_effect=Exception("fail"))
        instance.close = AsyncMock()
        # Mock DB config
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_request.app.state.db.get_collection.return_value = mock_collection
        result = await fetch_user_posts(mock_request, body, mock_user)
        assert isinstance(result, ListResponse)
        assert result.entities == []
        instance.close.assert_awaited_once()
        mock_request.app.state.logger.error.assert_called()


@pytest.mark.asyncio
async def test_fetch_user_posts_api_init_fail(mock_request, mock_user):
    body = RedditUsersRequest(usernames=["user1"], limit=2)
    with patch("app.modules.reddit.fetch_user_posts.RedditApi", return_value=None):
        with pytest.raises(InternalServerErrorException):
            await fetch_user_posts(mock_request, body, mock_user)


@pytest.mark.asyncio
async def test_fetch_user_posts_blocked_users_filtering(mock_request, mock_user):
    body = RedditUsersRequest(usernames=["user1"], limit=3)
    # Create posts with different authors
    post1 = MagicMock(spec=RedditPost)
    post1.author = "good_user"
    post2 = MagicMock(spec=RedditPost)
    post2.author = "blocked_user"
    post3 = MagicMock(spec=RedditPost)
    post3.author = "another_good"
    posts = [post1, post2, post3]
    with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_user_posts = AsyncMock(return_value=posts)
        instance.close = AsyncMock()
        # Mock DB config with blocked_users
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(
            return_value={"blocked_users": ["blocked_user"]}
        )
        mock_request.app.state.db.get_collection.return_value = mock_collection
        result = await fetch_user_posts(mock_request, body, mock_user)
        assert isinstance(result, ListResponse)
        # Only posts not by blocked_user should remain
        authors = [p.author for p in result.entities]
        assert "blocked_user" not in authors
        assert set(authors) == {"good_user", "another_good"}
        instance.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_user_posts_no_blocked_users_key(mock_request, mock_user):
    body = RedditUsersRequest(usernames=["user1"], limit=2)
    post1 = MagicMock(spec=RedditPost)
    post1.author = "userA"
    posts = [post1]
    with patch("app.modules.reddit.fetch_user_posts.RedditApi") as mock_api:
        instance = mock_api.return_value
        instance.fetch_user_posts = AsyncMock(return_value=posts)
        instance.close = AsyncMock()
        # Mock DB config with no blocked_users key
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value={})
        mock_request.app.state.db.get_collection.return_value = mock_collection
        result = await fetch_user_posts(mock_request, body, mock_user)
        assert isinstance(result, ListResponse)
        assert result.entities == posts
        instance.close.assert_awaited_once()
