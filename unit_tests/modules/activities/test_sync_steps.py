import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.activities.sync_steps import sync_steps
from app.common.responses import InternalServerErrorException
from app.modules.activities.activities_types import StepsSyncResponse, StepsItem


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


@pytest.fixture
def mock_collections():
    """Return separate mocks for steps and sync_meta collections."""
    steps_collection = AsyncMock()
    steps_collection.count_documents = AsyncMock(return_value=0)
    steps_collection.find_one = AsyncMock(return_value=None)
    steps_collection.insert_one = AsyncMock()

    sync_meta_collection = AsyncMock()
    sync_meta_collection.find_one = AsyncMock(return_value=None)
    sync_meta_collection.insert_one = AsyncMock()
    sync_meta_collection.update_one = AsyncMock()

    return steps_collection, sync_meta_collection


def setup_collection_side_effect(mock_request, steps_collection, sync_meta_collection):
    """Configure db.get_collection to return the appropriate mock per collection name."""

    def side_effect(name):
        if name == "steps":
            return steps_collection
        elif name == "steps_sync_meta":
            return sync_meta_collection
        return AsyncMock()

    mock_request.app.state.db.get_collection.side_effect = side_effect


@pytest.mark.asyncio
async def test_sync_steps_first_time(mock_request, mock_user, mock_collections):
    """First-time sync: no meta doc exists, all fetched items are new."""
    steps_collection, sync_meta_collection = mock_collections
    setup_collection_side_effect(mock_request, steps_collection, sync_meta_collection)

    mock_sync_api = AsyncMock()
    mock_sync_api.fetch_steps = AsyncMock(
        return_value=[
            StepsItem(steps=5000, date="2026-05-01"),
            StepsItem(steps=6000, date="2026-05-02"),
            StepsItem(steps=7000, date="2026-05-03"),
        ]
    )

    with patch(
        "app.modules.activities.sync_steps.StepsSyncApi", return_value=mock_sync_api
    ):
        result = await sync_steps(mock_request, mock_user)

    assert isinstance(result, StepsSyncResponse)
    assert result.days_synced == 3
    assert result.total_days == 3

    # Meta doc created since none existed
    sync_meta_collection.insert_one.assert_called_once_with(
        {"user_id": "user123", "last_synced_day": None}
    )

    # fetch_steps called without from_date (first-time sync)
    mock_sync_api.fetch_steps.assert_called_once_with()

    # Each item checked for duplicates
    assert steps_collection.find_one.await_count == 3

    # Each item inserted
    assert steps_collection.insert_one.await_count == 3

    # last_synced_day updated after each insert
    assert sync_meta_collection.update_one.await_count == 3


@pytest.mark.asyncio
async def test_sync_steps_incremental(mock_request, mock_user, mock_collections):
    """Incremental sync: meta exists, some items already in DB, some new."""
    steps_collection, sync_meta_collection = mock_collections
    setup_collection_side_effect(mock_request, steps_collection, sync_meta_collection)

    # Meta exists with last_synced_day
    sync_meta_collection.find_one.return_value = {
        "user_id": "user123",
        "last_synced_day": "2026-05-20",
    }
    steps_collection.count_documents.return_value = 2

    mock_sync_api = AsyncMock()
    mock_sync_api.fetch_steps = AsyncMock(
        return_value=[
            StepsItem(steps=5000, date="2026-05-21"),
            StepsItem(steps=6000, date="2026-05-22"),
            StepsItem(steps=7000, date="2026-05-23"),
            StepsItem(steps=8000, date="2026-05-24"),
            StepsItem(steps=9000, date="2026-05-25"),
        ]
    )

    # First two dates already exist, last three are new
    def find_one_side_effect(query):
        if query["date"] in ("2026-05-21", "2026-05-22"):
            return {"user_id": "user123", "date": query["date"], "steps": 5000}
        return None

    steps_collection.find_one.side_effect = find_one_side_effect

    with patch(
        "app.modules.activities.sync_steps.StepsSyncApi", return_value=mock_sync_api
    ):
        result = await sync_steps(mock_request, mock_user)

    assert isinstance(result, StepsSyncResponse)
    assert result.days_synced == 3  # 3 new items
    assert result.total_days == 5  # 2 existing + 3 new

    # fetch_steps called with from_date = day after last_synced_day
    mock_sync_api.fetch_steps.assert_called_once_with(from_date="2026-05-21")

    # No meta insert (already existed)
    sync_meta_collection.insert_one.assert_not_called()

    # All 5 items checked for duplicates
    assert steps_collection.find_one.await_count == 5

    # 3 new items inserted
    assert steps_collection.insert_one.await_count == 3

    # last_synced_day updated 3 times
    assert sync_meta_collection.update_one.await_count == 3


@pytest.mark.asyncio
async def test_sync_steps_meta_exists_none_last_synced(
    mock_request, mock_user, mock_collections
):
    """Meta doc exists but last_synced_day is None → behaves like first-time sync."""
    steps_collection, sync_meta_collection = mock_collections
    setup_collection_side_effect(mock_request, steps_collection, sync_meta_collection)

    sync_meta_collection.find_one.return_value = {
        "user_id": "user123",
        "last_synced_day": None,
    }
    steps_collection.count_documents.return_value = 0

    mock_sync_api = AsyncMock()
    mock_sync_api.fetch_steps = AsyncMock(
        return_value=[
            StepsItem(steps=5000, date="2026-05-01"),
        ]
    )

    with patch(
        "app.modules.activities.sync_steps.StepsSyncApi", return_value=mock_sync_api
    ):
        result = await sync_steps(mock_request, mock_user)

    assert isinstance(result, StepsSyncResponse)
    assert result.days_synced == 1
    assert result.total_days == 1

    # No insert (meta already existed)
    sync_meta_collection.insert_one.assert_not_called()

    # fetch_steps called without from_date (last_synced_day is None)
    mock_sync_api.fetch_steps.assert_called_once_with()


@pytest.mark.asyncio
async def test_sync_steps_no_new_data(mock_request, mock_user, mock_collections):
    """Sync returns empty list → nothing to sync."""
    steps_collection, sync_meta_collection = mock_collections
    setup_collection_side_effect(mock_request, steps_collection, sync_meta_collection)

    sync_meta_collection.find_one.return_value = {
        "user_id": "user123",
        "last_synced_day": "2026-05-20",
    }
    steps_collection.count_documents.return_value = 10

    mock_sync_api = AsyncMock()
    mock_sync_api.fetch_steps = AsyncMock(return_value=[])

    with patch(
        "app.modules.activities.sync_steps.StepsSyncApi", return_value=mock_sync_api
    ):
        result = await sync_steps(mock_request, mock_user)

    assert isinstance(result, StepsSyncResponse)
    assert result.days_synced == 0
    assert result.total_days == 10

    # No inserts or updates
    steps_collection.insert_one.assert_not_called()
    sync_meta_collection.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_sync_steps_all_existing(mock_request, mock_user, mock_collections):
    """All returned items already exist in DB → nothing to sync."""
    steps_collection, sync_meta_collection = mock_collections
    setup_collection_side_effect(mock_request, steps_collection, sync_meta_collection)

    sync_meta_collection.find_one.return_value = {
        "user_id": "user123",
        "last_synced_day": "2026-05-20",
    }
    steps_collection.count_documents.return_value = 10

    mock_sync_api = AsyncMock()
    mock_sync_api.fetch_steps = AsyncMock(
        return_value=[
            StepsItem(steps=5000, date="2026-05-21"),
            StepsItem(steps=6000, date="2026-05-22"),
        ]
    )

    # Both dates already exist
    steps_collection.find_one.return_value = {
        "user_id": "user123",
        "date": "2026-05-21",
        "steps": 5000,
    }

    with patch(
        "app.modules.activities.sync_steps.StepsSyncApi", return_value=mock_sync_api
    ):
        result = await sync_steps(mock_request, mock_user)

    assert isinstance(result, StepsSyncResponse)
    assert result.days_synced == 0
    assert result.total_days == 10

    steps_collection.insert_one.assert_not_called()
    sync_meta_collection.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_sync_steps_internal_error(mock_request, mock_user, mock_collections):
    """fetch_steps raises an exception → InternalServerErrorException."""
    steps_collection, sync_meta_collection = mock_collections
    setup_collection_side_effect(mock_request, steps_collection, sync_meta_collection)

    sync_meta_collection.find_one.return_value = None
    steps_collection.count_documents.return_value = 0

    mock_sync_api = AsyncMock()
    mock_sync_api.fetch_steps = AsyncMock(side_effect=Exception("API unavailable"))

    with patch(
        "app.modules.activities.sync_steps.StepsSyncApi", return_value=mock_sync_api
    ):
        with pytest.raises(InternalServerErrorException):
            await sync_steps(mock_request, mock_user)

    mock_request.app.state.logger.error.assert_any_call(
        "Error syncing steps for user user123: API unavailable"
    )
