import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.activities.update_goals import update_goals
from app.common.responses import NotFoundException, InternalServerErrorException
from app.modules.activities.activities_types import GoalsRequest, ActivitiesConfig


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
    body = MagicMock(spec=GoalsRequest)
    body.model_dump.return_value = {"walk_weekly_goal": 1000}
    return body


@pytest.mark.asyncio
async def test_update_goals_success(mock_request, mock_user, mock_body):
    update_result = MagicMock()
    update_result.matched_count = 1
    updated_data = {
        "id": "cfg1",
        "walk_weekly_goal": 1000,
        "walk_monthly_goal": 4000,
        "cycling_weekly_goal": 200,
        "cycling_monthly_goal": 800,
        "chores": [],
    }
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(return_value=update_result)
    collection.find_one = AsyncMock(return_value=updated_data)

    result = await update_goals(mock_request, mock_body, mock_user)
    mock_request.app.state.db.get_collection.assert_called_with("activities")
    collection.update_one.assert_called_once()
    collection.find_one.assert_called_once_with({"user_id": mock_user.id})
    assert isinstance(result, ActivitiesConfig)
    assert result.walk_weekly_goal == 1000
    assert result.id == "cfg1"


@pytest.mark.asyncio
async def test_update_goals_not_found(mock_request, mock_user, mock_body):
    update_result = MagicMock()
    update_result.matched_count = 0
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(return_value=update_result)

    with pytest.raises(NotFoundException):
        await update_goals(mock_request, mock_body, mock_user)
    mock_request.app.state.logger.error.assert_called_with(
        f"Failed to update activity goals for user {mock_user.id}"
    )


@pytest.mark.asyncio
async def test_update_goals_internal_error(mock_request, mock_user, mock_body):
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(side_effect=Exception("db error"))

    with pytest.raises(InternalServerErrorException):
        await update_goals(mock_request, mock_body, mock_user)
    mock_request.app.state.logger.error.assert_any_call(
        f"Error updating activity goals for user {mock_user.id}: db error"
    )
