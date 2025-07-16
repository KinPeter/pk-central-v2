import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.data_backup.email_backup import email_backup
from app.common.responses import InternalServerErrorException, MessageResponse


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.db = MagicMock()
    req.app.state.env = MagicMock()
    req.app.state.logger = MagicMock()
    return req


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user123"
    return user


@pytest.mark.asyncio
async def test_email_backup_success(mock_request, mock_user):
    db = mock_request.app.state.db
    # Mock all DB calls to return dummy data
    db.get_collection.return_value.find_one = AsyncMock(
        return_value={"email": "test@pk.com", "name": "Peter", "_id": "id"}
    )
    db.get_collection.return_value.find = MagicMock(
        return_value=MagicMock(to_list=AsyncMock(return_value=[{"_id": "id"}]))
    )
    # Patch EmailManager and EmailAttachment
    with patch(
        "app.modules.data_backup.email_backup.EmailManager"
    ) as MockEmailManager, patch(
        "app.modules.data_backup.email_backup.EmailAttachment"
    ) as MockEmailAttachment:
        mock_email_manager = MockEmailManager.return_value
        mock_email_manager.send_data_backup.return_value = None
        # Call the function
        result = await email_backup(mock_request, mock_user)
        assert isinstance(result, MessageResponse)
        assert result.message == "Data backup email sent successfully."
        mock_email_manager.send_data_backup.assert_called_once()
        # Check DB call counts
        # There are 4 find_one calls (users, start_settings, activities, reddit)
        # and 9 find calls (flights, visits, notes, personal_data, shortcuts, birthdays, aircrafts, airlines, airports)
        assert db.get_collection.return_value.find_one.call_count == 4
        assert db.get_collection.return_value.find.call_count == 9


@pytest.mark.asyncio
async def test_email_backup_no_email(mock_request, mock_user):
    db = mock_request.app.state.db
    db.get_collection.return_value.find_one = AsyncMock(return_value=None)
    db.get_collection.return_value.find = MagicMock(
        return_value=MagicMock(to_list=AsyncMock(return_value=[]))
    )
    with patch("app.modules.data_backup.email_backup.EmailManager") as MockEmailManager:
        with pytest.raises(InternalServerErrorException):
            await email_backup(mock_request, mock_user)
        mock_request.app.state.logger.error.assert_called()


@pytest.mark.asyncio
async def test_email_backup_db_error(mock_request, mock_user):
    db = mock_request.app.state.db
    db.get_collection.return_value.find_one = AsyncMock(
        side_effect=Exception("db fail")
    )
    with patch("app.modules.data_backup.email_backup.EmailManager") as MockEmailManager:
        with pytest.raises(InternalServerErrorException):
            await email_backup(mock_request, mock_user)
        mock_request.app.state.logger.error.assert_called()
