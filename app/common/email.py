import smtplib
from email.message import EmailMessage
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, NotImplementedException


class EmailData:
    def __init__(self, subject: str, to: str, text: str, html: str):
        self.subject = subject
        self.to = to
        self.text = text
        self.html = html


class EmailManager:
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
        <p>As requested, please find attached the backup file of your data.</p>
        """
        text = f"""
        Hey {name}!
        As requested, please find attached the backup file of your data.
        """
        return (text, html)
