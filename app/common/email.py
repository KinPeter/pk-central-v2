from datetime import date
import smtplib
import requests

from email.message import EmailMessage

from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, NotImplementedException


class EmailAttachment:
    def __init__(self, content: str, filename: str):
        self.content = content
        self.filename = filename


class PkMailData:
    def __init__(
        self,
        subject: str,
        to: str,
        html: str,
        attachments: list[EmailAttachment] | None = None,
    ):
        self.subject = subject
        self.to = to
        self.html = html
        self.attachments = attachments


class EmailManager:
    def __init__(self, env: PkCentralEnv):
        self.url = env.MAILER_URL
        self.api_key = env.MAILER_API_KEY
        self.notification_email = env.NOTIFICATION_EMAIL
        self.templates = EmailTemplates(env)

    def send_signup_notification(self, email: str):
        subject = "A user signed up to PK-Central"
        text, html = self.templates.signup_notification(email)
        email_data = PkMailData(subject, self.notification_email, html)
        self.send_email(email_data)

    def send_login_code(self, email: str, login_code: str):
        subject = f"{login_code} - Log in to PK-Central"
        text, html = self.templates.login_code(login_code)
        email_data = PkMailData(subject, email, html)
        self.send_email(email_data)

    def send_data_backup(
        self,
        name: str,
        email: str,
        files: list[EmailAttachment],
    ):
        today_str = date.today().strftime("%Y-%m-%d")
        subject = f"Data backup for PK-Central {today_str}"
        text, html = self.templates.data_backup(name)
        email_data = PkMailData(
            subject=subject,
            to=email,
            html=html,
            attachments=files,
        )
        self.send_email(email_data)

    def send_email(self, email_data: PkMailData):
        # Need to fake the user agent because tarhelypark blocks python-requests
        headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
        payload: dict[str, str | list[dict]] = {
            "apiKey": self.api_key,
            "subject": email_data.subject,
            "to": email_data.to,
            "html": email_data.html,
        }

        if email_data.attachments and len(email_data.attachments) > 0:
            payload["attachments"] = [
                {"content": att.content, "filename": att.filename}
                for att in email_data.attachments
            ]

        try:
            response = requests.post(
                self.url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise InternalServerErrorException(
                f"Failed to send email to {email_data.to}: {e}"
            )


class EmailData:
    def __init__(self, subject: str, to: str, text: str, html: str):
        self.subject = subject
        self.to = to
        self.text = text
        self.html = html


class SmtpLibEmailManager:
    """
    DigitalOcean is blocking all SMTP ports, so this is not used for now.
    Use the HTTP-based EmailManager instead.
    """

    def __init__(self, env: PkCentralEnv):
        self.notification_email = env.NOTIFICATION_EMAIL
        self.email_host = env.EMAIL_HOST
        self.email_user = env.EMAIL_USER
        self.email_pass = env.EMAIL_PASS
        self.templates = EmailTemplates(env)

    def send_signup_notification(self, email: str):
        subject = "A user signed up to PK-Central"
        text, html = self.templates.signup_notification(email)
        email_data = EmailData(subject, self.notification_email, text, html)
        self.send_email(email_data)

    def send_login_code(self, email: str, login_code: str):
        subject = f"{login_code} - Log in to PK-Central"
        text, html = self.templates.login_code(login_code)
        email_data = EmailData(subject, email, text, html)
        self.send_email(email_data)

    def send_data_backup(self, name: str):
        # FIXME - Implement data backup email functionality first
        raise NotImplementedException(
            "Data backup email functionality is not implemented yet."
        )
        # subject = "Data backup for PK Central"
        # text, html = self.templates.data_backup(name)
        # email_data = EmailData(subject, self.notification_email, text, html)
        # self.send_email(email_data)

    def send_email(self, email_data: EmailData):
        msg = EmailMessage()
        msg["Subject"] = email_data.subject
        msg["From"] = f'"P-Kin.com" <{self.email_user}>'
        msg["To"] = email_data.to
        msg.set_content(email_data.text)
        msg.add_alternative(email_data.html, subtype="html")

        try:
            with smtplib.SMTP_SSL(self.email_host, 465) as server:
                server.login(self.email_user, self.email_pass)
                server.send_message(msg)
        except Exception as e:
            raise InternalServerErrorException(
                f"Failed to send email to {email_data.to}: {e}"
            )


class EmailTemplates:
    def __init__(self, env: PkCentralEnv):
        self.env = env

    def login_code(self, login_code: str) -> tuple[str, str]:
        expires_in_minutes = self.env.LOGIN_CODE_EXPIRY
        html = f"""
        <h3>Hello!</h3>
        <p>Please use the code below to log in, it expires in {expires_in_minutes} minutes.</p>
        <h1>{login_code}</h1>
        """
        text = f"""
        Hello!
        Your code to log in: {login_code}.
        You can use it within the next {expires_in_minutes} minutes.
        """
        return (text, html)

    def signup_notification(self, email: str) -> tuple[str, str]:
        html = f"""
        <h3>Hey Peter!</h3>
        <p>A user just signed up to PK-Central:</p>
        <p>Email: {email}</p>
        """
        text = f"""
        Hey Peter!
        A user just signed up to PK-Central:
        Email: {email}
        """
        return (text, html)

    def data_backup(self, name: str) -> tuple[str, str]:
        html = f"""
        <h3>Hey {name}!</h3>
        <p>As requested, please find attached the backup files of your data.</p>
        """
        text = f"""
        Hey {name}!
        As requested, please find attached the backup files of your data.
        """
        return (text, html)
