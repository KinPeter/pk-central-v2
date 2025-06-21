import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.reddit.reddit_utils import create_initial_reddit_config, parse_post
from app.modules.reddit.reddit_types import RedditPost


class TestCreateInitialRedditConfig:
    @pytest.fixture
    def db(self):
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.get_collection.return_value = mock_collection
        return mock_db

    @pytest.fixture
    def logger(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_create_initial_reddit_config_success(self, db, logger):
        db.get_collection.return_value.find_one = AsyncMock(return_value=None)
        db.get_collection.return_value.insert_one = AsyncMock()
        user_id = "user123"
        await create_initial_reddit_config(db, logger, user_id)
        db.get_collection.return_value.insert_one.assert_awaited_once()
        logger.info.assert_called_with(
            f"Initial Reddit config created for user {user_id}"
        )

    @pytest.mark.asyncio
    async def test_create_initial_reddit_config_already_exists(self, db, logger):
        db.get_collection.return_value.find_one = AsyncMock(
            return_value={"user_id": "user123"}
        )
        user_id = "user123"
        with pytest.raises(
            ValueError, match="Reddit config already exists for user user123"
        ):
            await create_initial_reddit_config(db, logger, user_id)
        logger.warning.assert_called_with(
            f"Reddit config already exists for user {user_id}"
        )
        db.get_collection.return_value.insert_one.assert_not_awaited()


class TestParsePost:
    @pytest.fixture
    def logger(self):
        return MagicMock()

    def test_parse_post_image(self, logger):
        submission = MagicMock()
        submission.url = "https://example.com/image.jpg"
        submission.title = "Test Image"
        submission.author.name = "testuser"
        submission.subreddit.display_name = "testsubreddit"

        posts = parse_post(submission, logger)
        assert len(posts) == 1
        assert isinstance(posts[0], RedditPost)
        assert posts[0].title == "Test Image"
        assert posts[0].url == "https://example.com/image.jpg"
        assert posts[0].author == "testuser"
        assert posts[0].subreddit == "testsubreddit"

    def test_parse_post_gallery(self, logger):
        submission = MagicMock()
        submission.url = "https://example.com/gallery"
        submission.gallery_data = {"items": [{"media_id": "123"}, {"media_id": "456"}]}
        submission.media_metadata = {
            "123": {"m": "image/jpeg", "s": {"u": "https://example.com/image.jpg"}},
            "456": {"m": "image/jpeg", "s": {"u": "https://example.com/image2.jpg"}},
        }
        submission.title = "Test Gallery"
        submission.author.name = "testuser"
        submission.subreddit.display_name = "testsubreddit"

        posts = parse_post(submission, logger)
        assert len(posts) == 2
        assert isinstance(posts[0], RedditPost)
        assert isinstance(posts[1], RedditPost)
        assert posts[0].title == "Test Gallery"
        assert posts[0].url == "https://example.com/image.jpg"
        assert posts[0].author == "testuser"
        assert posts[0].subreddit == "testsubreddit"
        assert posts[1].title == "Test Gallery"
        assert posts[1].url == "https://example.com/image2.jpg"
        assert posts[1].author == "testuser"
        assert posts[1].subreddit == "testsubreddit"

    def test_parse_post_no_image_or_gallery(self, logger):
        submission = MagicMock()
        submission.url = "https://example.com/textpost"
        submission.title = "Test Text"
        submission.author.name = "testuser"
        submission.subreddit.display_name = "testsubreddit"
        # No gallery_data or media_metadata attributes
        posts = parse_post(submission, logger)
        assert posts == []

    def test_parse_post_error_handling(self, logger):
        submission = MagicMock()
        # Simulate an error by making .url raise an exception
        type(submission).url = property(
            lambda self: (_ for _ in ()).throw(Exception("fail"))
        )
        posts = parse_post(submission, logger)
        assert posts == []
        logger.error.assert_called()
