import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.activities.activities_utils import create_initial_activities_config


class TestCreateInitialActivitiesConfig:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        collection = AsyncMock()
        db.get_collection.return_value = collection
        return db, collection

    @pytest.fixture
    def mock_logger(self):
        return MagicMock()

    @pytest.fixture
    def user_id(self):
        return "user123"

    @pytest.mark.asyncio
    async def test_create_initial_activities_config_success(
        self, mock_db, mock_logger, user_id
    ):
        db, collection = mock_db
        collection.find_one.return_value = None
        logger = mock_logger

        await create_initial_activities_config(db, logger, user_id)

        db.get_collection.assert_any_call("activities")
        collection.find_one.assert_awaited_with({"user_id": user_id})
        assert collection.insert_one.await_count == 1
        logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_create_initial_activities_config_already_exists(
        self, mock_db, mock_logger, user_id
    ):
        db, collection = mock_db
        collection.find_one.return_value = {"user_id": user_id}
        logger = mock_logger

        with pytest.raises(ValueError):
            await create_initial_activities_config(db, logger, user_id)

        db.get_collection.assert_any_call("activities")
        collection.find_one.assert_awaited_with({"user_id": user_id})
        logger.warning.assert_called()
        collection.insert_one.assert_not_awaited()
