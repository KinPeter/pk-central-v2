import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.activities.delete_chore import delete_chore
from app.common.responses import NotFoundException, InternalServerErrorException
from app.modules.activities.activities_types import ActivitiesConfig


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
async def test_delete_chore_success(mock_request, mock_user):
    update_result = MagicMock()
    update_result.matched_count = 1
    updated_data = {
        "id": "cfg1",
        "created_at": "2024-01-01T00:00:00Z",
        "walk_weekly_goal": 1000,
        "walk_monthly_goal": 4000,
        "cycling_weekly_goal": 200,
        "cycling_monthly_goal": 800,
        "chores": [],
    }
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(return_value=update_result)
    collection.find_one = AsyncMock(return_value=updated_data)

    result = await delete_chore(mock_request, "chore1", mock_user)
    mock_request.app.state.db.get_collection.assert_called_with("activities")
    collection.update_one.assert_called_once()
    collection.find_one.assert_called_once_with({"user_id": mock_user.id})
    assert isinstance(result, ActivitiesConfig)
    assert result.chores == []
    assert result.id == "cfg1"


@pytest.mark.asyncio
async def test_delete_chore_not_found(mock_request, mock_user):
    update_result = MagicMock()
    update_result.matched_count = 0
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(return_value=update_result)

    with pytest.raises(NotFoundException):
        await delete_chore(mock_request, "chore1", mock_user)
    mock_request.app.state.logger.error.assert_called_with(
        f"Failed to delete chore chore1 for user {mock_user.id}, config not found"
    )


@pytest.mark.asyncio
async def test_delete_chore_internal_error(mock_request, mock_user):
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(side_effect=Exception("db error"))

    with pytest.raises(InternalServerErrorException):
        await delete_chore(mock_request, "chore1", mock_user)
    mock_request.app.state.logger.error.assert_any_call(
        f"Error deleting chore chore1 for user {mock_user.id}: db error"
    )
