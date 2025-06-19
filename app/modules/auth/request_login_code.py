from logging import Logger
from fastapi import Request
from app.common.email import EmailManager
from app.common.environment import PkCentralEnv
from app.common.responses import (
    ForbiddenOperationException,
    InternalServerErrorException,
    MessageResponse,
)
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import EmailLoginRequest
from app.modules.auth.user_utils import sign_up_or_login_user


async def request_login_code(
    body: EmailLoginRequest, request: Request
) -> MessageResponse:
    env: PkCentralEnv = request.app.state.env
    logger: Logger = request.app.state.logger
    db: AsyncDatabase = request.app.state.db
    email_manager = EmailManager(env)
    email = body.email.lower().strip()

    is_restricted = env.EMAILS_ALLOWED is not None and env.EMAILS_ALLOWED != "all"
    if is_restricted and email not in env.EMAILS_ALLOWED.split(","):
        raise ForbiddenOperationException("Sign up")

    try:
        await sign_up_or_login_user(
            email=email,
            send_emails=True,
            env=env,
            db=db,
            email_manager=email_manager,
            logger=logger,
        )

        return MessageResponse(message="Check your inbox")

    except Exception as e:
        logger.error(f"Error requesting login code for {email}: {e}")
        raise InternalServerErrorException(
            "An error occurred while requesting the login code. Please try again later."
            + str(e)
        )
