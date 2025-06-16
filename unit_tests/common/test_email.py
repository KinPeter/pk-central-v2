import pytest
from unittest.mock import MagicMock, patch
from app.common.email import EmailManager, EmailData
from app.common.responses import InternalServerErrorException, NotImplementedException


@pytest.fixture
def env():
    mock_env = MagicMock()
    mock_env.NOTIFICATION_EMAIL = "notify@pk.com"
    mock_env.EMAIL_HOST = "smtp.pk.com"
    mock_env.EMAIL_USER = "user@pk.com"
    mock_env.EMAIL_PASS = "password"
    return mock_env


@pytest.fixture
def email_manager(env):
    with patch("app.common.email.EmailTemplates") as mock_templates:
        mock_templates.return_value.signup_notification.return_value = ("text", "html")
        mock_templates.return_value.login_code.return_value = ("text", "html")
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


def test_send_data_backup_raises_not_implemented(email_manager):
    with pytest.raises(NotImplementedException):
        email_manager.send_data_backup("backup.zip")


def test_send_email_success(env):
    email_manager = EmailManager(env)
    email_data = EmailData("subject", "to@pk.com", "text", "<b>html</b>")
    with patch("app.common.email.smtplib.SMTP_SSL") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        email_manager.send_email(email_data)
        mock_server.login.assert_called_once_with(env.EMAIL_USER, env.EMAIL_PASS)
        mock_server.send_message.assert_called_once()


def test_send_email_raises_on_error(env):
    email_manager = EmailManager(env)
    email_data = EmailData("subject", "to@pk.com", "text", "<b>html</b>")
    with patch("app.common.email.smtplib.SMTP", side_effect=Exception("fail")):
        with pytest.raises(InternalServerErrorException):
            email_manager.send_email(email_data)
