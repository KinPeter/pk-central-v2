import pytest
from unittest.mock import AsyncMock, MagicMock
from app.common.db import MongoDbManager


@pytest.fixture
def env():
    mock_env = MagicMock()
    mock_env.MONGODB_URI = "mongodb://localhost:27017"
    mock_env.MONGODB_NAME = "testdb"
    return mock_env


@pytest.fixture
def logger():
    return MagicMock()


@pytest.mark.asyncio
async def test_connect_calls_initiate_and_returns_db(env, logger):
    manager = MongoDbManager(env, logger)
    manager._initiate = AsyncMock()
    manager.db = MagicMock()
    result = await manager.connect()
    manager._initiate.assert_awaited_once()
    assert result == manager.db


@pytest.mark.asyncio
async def test_connect_raises_if_db_is_none(env, logger):
    manager = MongoDbManager(env, logger)
    manager._initiate = AsyncMock()
    manager.db = None
    with pytest.raises(ValueError, match="No MongoDB instance after initiation."):
        await manager.connect()


@pytest.mark.asyncio
async def test_close_calls_client_close_and_logs(env, logger):
    manager = MongoDbManager(env, logger)
    mock_client = AsyncMock()
    manager.mongo_client = mock_client
    await manager.close()
    mock_client.close.assert_awaited_once()
    logger.info.assert_called_with("MongoDB connection closed.")


@pytest.mark.asyncio
async def test_close_does_nothing_if_no_client(env, logger):
    manager = MongoDbManager(env, logger)
    manager.mongo_client = None
    await manager.close()
    logger.info.assert_not_called()
