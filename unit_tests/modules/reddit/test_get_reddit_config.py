import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.reddit.get_reddit_config import get_reddit_config
from app.common.responses import NotFoundException, InternalServerErrorException
from app.modules.reddit.reddit_types import RedditConfig


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.db = MagicMock()
    req.app.state.logger = MagicMock()
    return req


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user123"
    return user


@pytest.mark.asyncio
async def test_get_reddit_config_success(mock_request, mock_user):
    mock_set = {"name": "set1", "subs": ["funny"], "usernames": []}
    config_data = {
        "id": "cfg1",
        "sets": [mock_set],
        "blocked_users": ["baduser"],
        "user_id": mock_user.id,
    }
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        return_value=config_data
    )
    result = await get_reddit_config(mock_request, mock_user)
    assert isinstance(result, RedditConfig)
    assert result.id == "cfg1"
    assert isinstance(result.sets, list)
    assert len(result.sets) == 1
    assert result.sets[0].name == "set1"
    assert result.sets[0].subs == ["funny"]
    assert result.sets[0].usernames == []
    assert result.blocked_users == ["baduser"]


@pytest.mark.asyncio
async def test_get_reddit_config_not_found(mock_request, mock_user):
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        return_value=None
    )
    with pytest.raises(NotFoundException):
        await get_reddit_config(mock_request, mock_user)
    mock_request.app.state.logger.error.assert_called_with(
        f"Reddit configuration not found for user {mock_user.id}"
    )


@pytest.mark.asyncio
async def test_get_reddit_config_internal_error(mock_request, mock_user):
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        side_effect=Exception("db error")
    )
    with pytest.raises(InternalServerErrorException):
        await get_reddit_config(mock_request, mock_user)
    mock_request.app.state.logger.error.assert_any_call(
        f"Error retrieving Reddit configuration for user {mock_user.id}: db error"
    )
