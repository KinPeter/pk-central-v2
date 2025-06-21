import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.reddit.update_reddit_config import update_reddit_config
from app.common.responses import NotFoundException, InternalServerErrorException
from app.modules.reddit.reddit_types import RedditConfigRequest, RedditConfig


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


@pytest.fixture
def mock_body():
    body = MagicMock(spec=RedditConfigRequest)
    body.model_dump.return_value = {
        "sets": [{"name": "set1", "subs": ["funny"], "usernames": ["alice"]}],
        "blocked_users": ["baduser"],
    }
    return body


@pytest.mark.asyncio
async def test_update_reddit_config_success(mock_request, mock_user, mock_body):
    mock_update_result = MagicMock()
    mock_update_result.matched_count = 1
    mock_request.app.state.db.get_collection.return_value.update_one = AsyncMock(
        return_value=mock_update_result
    )
    updated_config = {
        "id": "cfg1",
        "created_at": "2024-01-01T00:00:00Z",
        "sets": [{"name": "set1", "subs": ["funny"], "usernames": ["alice"]}],
        "blocked_users": ["baduser"],
        "user_id": mock_user.id,
    }
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        return_value=updated_config
    )
    result = await update_reddit_config(mock_request, mock_body, mock_user)
    assert isinstance(result, RedditConfig)
    assert result.id == "cfg1"
    assert isinstance(result.sets, list)
    assert len(result.sets) == 1
    assert result.sets[0].name == "set1"
    assert result.sets[0].subs == ["funny"]
    assert result.sets[0].usernames == ["alice"]
    assert result.blocked_users == ["baduser"]


@pytest.mark.asyncio
async def test_update_reddit_config_not_found(mock_request, mock_user, mock_body):
    mock_update_result = MagicMock()
    mock_update_result.matched_count = 0
    mock_request.app.state.db.get_collection.return_value.update_one = AsyncMock(
        return_value=mock_update_result
    )
    with pytest.raises(NotFoundException):
        await update_reddit_config(mock_request, mock_body, mock_user)
    mock_request.app.state.logger.error.assert_called_with(
        f"Failed to update Reddit configuration for user {mock_user.id}"
    )


@pytest.mark.asyncio
async def test_update_reddit_config_internal_error(mock_request, mock_user, mock_body):
    mock_request.app.state.db.get_collection.return_value.update_one = AsyncMock(
        side_effect=Exception("db error")
    )
    with pytest.raises(InternalServerErrorException):
        await update_reddit_config(mock_request, mock_body, mock_user)
    mock_request.app.state.logger.error.assert_any_call(
        f"Error updating Reddit configuration for user {mock_user.id}: db error"
    )
