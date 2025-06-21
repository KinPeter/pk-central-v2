import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.reddit.reddit_utils import create_initial_reddit_config


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
