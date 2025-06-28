import pytest
from unittest.mock import AsyncMock, MagicMock
from app.common.responses import NotFoundException, InternalServerErrorException
from app.modules.activities.activities_types import ActivitiesConfig
from app.modules.activities.get_activities import get_activities


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.db = MagicMock()
    req.app.state.logger = MagicMock()
    req.app.state.env = MagicMock()
    return req


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user123"
    return user


@pytest.mark.asyncio
async def test_get_activities_success(mock_request, mock_user):
    data = {
        "id": "cfg1",
        "created_at": "2024-01-01T00:00:00Z",
        "chores": [
            {"id": "chore1", "name": "Chore1", "km_interval": 5, "last_km": 10.34}
        ],
        "walk_weekly_goal": 20,
        "walk_monthly_goal": 80,
        "cycling_weekly_goal": 50,
        "cycling_monthly_goal": 200,
    }
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        return_value=data
    )
    result = await get_activities(mock_request, mock_user)
    assert isinstance(result, ActivitiesConfig)
    assert result.id == "cfg1"
    assert result.chores[0].id == "chore1"
    assert result.chores[0].name == "Chore1"
    assert result.chores[0].km_interval == 5
    assert result.chores[0].last_km == 10.34
    assert result.walk_weekly_goal == 20
    assert result.walk_monthly_goal == 80
    assert result.cycling_weekly_goal == 50
    assert result.cycling_monthly_goal == 200


@pytest.mark.asyncio
async def test_get_activities_not_found(mock_request, mock_user):
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        return_value=None
    )
    with pytest.raises(NotFoundException):
        await get_activities(mock_request, mock_user)
    mock_request.app.state.logger.error.assert_called_with(
        f"Activities config not found for user {mock_user.id}"
    )


@pytest.mark.asyncio
async def test_get_activities_internal_error(mock_request, mock_user):
    mock_request.app.state.db.get_collection.return_value.find_one = AsyncMock(
        side_effect=Exception("db error")
    )
    with pytest.raises(InternalServerErrorException):
        await get_activities(mock_request, mock_user)
    mock_request.app.state.logger.error.assert_any_call(
        f"Error retrieving Activities config for user {mock_user.id}: db error"
    )
