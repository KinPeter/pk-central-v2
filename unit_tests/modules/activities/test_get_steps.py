import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone

from app.modules.activities.get_steps import get_steps
from app.common.responses import InternalServerErrorException, ListResponse
from app.modules.activities.activities_types import StepsItem


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


def _make_cursor(docs: list[dict]) -> AsyncMock:
    """Create an async cursor mock that returns the given docs via to_list."""
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=docs)
    return cursor


class TestGetSteps:
    @pytest.mark.asyncio
    async def test_get_steps_default_range(self, mock_request, mock_user):
        """No params given — returns last 30 days up to yesterday with mixed DB data and zero-fills."""
        collection = mock_request.app.state.db.get_collection.return_value
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        # Provide a couple of step records within the 30-day window
        mid_date = (datetime.now(timezone.utc) - timedelta(days=15)).strftime(
            "%Y-%m-%d"
        )
        collection.find.return_value = _make_cursor(
            [
                {"user_id": mock_user.id, "steps": 5000, "date": yesterday},
                {
                    "user_id": mock_user.id,
                    "steps": 3000,
                    "date": mid_date,
                },
            ]
        )

        result = await get_steps(mock_request, mock_user, None, None)

        assert isinstance(result, ListResponse)
        assert len(result.entities) == 30
        # The last entity should be yesterday with 5000 steps
        assert result.entities[-1].steps == 5000
        assert result.entities[-1].date == yesterday
        # A day without data should have 0 steps
        assert result.entities[0].steps == 0

        mock_request.app.state.db.get_collection.assert_called_with("steps")
        collection.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_steps_with_dates(self, mock_request, mock_user):
        """Specific date range — returns exactly that range with zero-fills."""
        collection = mock_request.app.state.db.get_collection.return_value

        # Only one day has data in the 5-day range
        collection.find.return_value = _make_cursor(
            [
                {
                    "user_id": mock_user.id,
                    "steps": 8000,
                    "date": "2026-01-03",
                },
            ]
        )

        result = await get_steps(mock_request, mock_user, "2026-01-01", "2026-01-05")

        assert isinstance(result, ListResponse)
        assert len(result.entities) == 5
        # Jan 1, 2, 4, 5 should be zero; Jan 3 should be 8000
        assert result.entities[0] == StepsItem(steps=0, date="2026-01-01")
        assert result.entities[1] == StepsItem(steps=0, date="2026-01-02")
        assert result.entities[2] == StepsItem(steps=8000, date="2026-01-03")
        assert result.entities[3] == StepsItem(steps=0, date="2026-01-04")
        assert result.entities[4] == StepsItem(steps=0, date="2026-01-05")

        mock_request.app.state.db.get_collection.assert_called_with("steps")
        collection.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_steps_no_data(self, mock_request, mock_user):
        """No step records in DB — all 30 days returned with 0 steps."""
        collection = mock_request.app.state.db.get_collection.return_value
        collection.find.return_value = _make_cursor([])

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        result = await get_steps(mock_request, mock_user, None, None)

        assert isinstance(result, ListResponse)
        assert len(result.entities) == 30
        # All entries should have 0 steps
        for item in result.entities:
            assert item.steps == 0
        # Last date should be yesterday
        assert result.entities[-1].date == yesterday

    @pytest.mark.asyncio
    async def test_get_steps_internal_error(self, mock_request, mock_user):
        """DB error — raises InternalServerErrorException."""
        collection = mock_request.app.state.db.get_collection.return_value
        collection.find.side_effect = Exception("db connection error")

        with pytest.raises(InternalServerErrorException):
            await get_steps(mock_request, mock_user, None, None)

        mock_request.app.state.logger.error.assert_called_once()
