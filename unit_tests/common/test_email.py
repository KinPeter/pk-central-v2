import pytest
import requests
from unittest.mock import MagicMock, patch
from app.common.email import EmailManager, PkMailData
from app.common.responses import InternalServerErrorException, NotImplementedException


@pytest.fixture
def env():
    mock_env = MagicMock()
    mock_env.NOTIFICATION_EMAIL = "notify@pk.com"
    mock_env.EMAIL_HOST = "smtp.pk.com"
    mock_env.EMAIL_USER = "user@pk.com"
    mock_env.EMAIL_PASS = "password"
    mock_env.MAILER_URL = "https://mailer.pk.com"
    mock_env.MAILER_API_KEY = "api-key"
    return mock_env


@pytest.fixture
def email_manager(env):
    with patch("app.common.email.EmailTemplates") as mock_templates:
        mock_templates.return_value.signup_notification.return_value = ("text", "html")
        mock_templates.return_value.login_code.return_value = ("text", "html")
        mock_templates.return_value.data_backup.return_value = ("text", "html")
        yield EmailManager(env)


def test_send_signup_notification_calls_send_email(email_manager):
    with patch.object(email_manager, "send_email") as mock_send_email:
        email_manager.send_signup_notification("test@user.com")
        mock_send_email.assert_called_once()
        email_data = mock_send_email.call_args[0][0]
        assert email_data.subject == "A user signed up to PK-Central"
        assert email_data.to == email_manager.notification_email


def test_send_login_code_calls_send_email(email_manager):
    with patch.object(email_manager, "send_email") as mock_send_email:
        email_manager.send_login_code("test@user.com", "123456")
        mock_send_email.assert_called_once()
        email_data = mock_send_email.call_args[0][0]
        assert "Log in to PK-Central" in email_data.subject
        assert email_data.to == "test@user.com"


def test_send_data_backup(email_manager):
    with patch.object(email_manager, "send_email") as mock_send_email:
        files = [
            MagicMock(content="file-content-1", filename="file1.json"),
            MagicMock(content="file-content-2", filename="file2.json"),
        ]
        email_manager.send_data_backup(name="Peter", email="peter@pk.com", files=files)
        mock_send_email.assert_called_once()
        email_data = mock_send_email.call_args[0][0]
        assert email_data.subject == "Data backup for PK-Central"
        assert email_data.to == "peter@pk.com"
        assert email_data.attachments == files


def test_send_email_success(env):
    email_manager = EmailManager(env)
    email_data = PkMailData("subject", "to@pk.com", "<b>html</b>")
    with patch("app.common.email.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        email_manager.send_email(email_data)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["to"] == "to@pk.com"
        assert kwargs["headers"]["User-Agent"] == "Mozilla/5.0"


def test_send_email_raises_on_error(env):
    email_manager = EmailManager(env)
    email_data = PkMailData("subject", "to@pk.com", "<b>html</b>")
    with patch(
        "app.common.email.requests.post",
        side_effect=requests.exceptions.RequestException("fail"),
    ):
        with pytest.raises(InternalServerErrorException):
            email_manager.send_email(email_data)
