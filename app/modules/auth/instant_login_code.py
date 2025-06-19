from logging import Logger
from fastapi import Request
from app.common.environment import PkCentralEnv
from app.common.responses import (
    ForbiddenOperationException,
    InternalServerErrorException,
)
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import EmailLoginRequest, LoginCodeResponse
from app.modules.auth.user_utils import sign_up_or_login_user


async def instant_login_code(
    body: EmailLoginRequest, request: Request
) -> LoginCodeResponse:
    env: PkCentralEnv = request.app.state.env
    logger: Logger = request.app.state.logger
    db: AsyncDatabase = request.app.state.db
    email = body.email.lower().strip()

    if env.PK_ENV.lower() not in ["dev", "test"]:
        raise ForbiddenOperationException(
            "Instant login code is only available in development environments."
        )

    try:
        login_code = await sign_up_or_login_user(
            email=email,
            send_emails=False,
            env=env,
            db=db,
            email_manager=None,
            logger=logger,
        )

        logger.warning(
            f"User {email} is getting an instant login code on environment '{env.PK_ENV}'"
        )

        return LoginCodeResponse(login_code=login_code)

    except Exception as e:
        logger.error(f"Error requesting instant login code for {email}: {e}")
        raise InternalServerErrorException(
            "An error occurred while requesting the login code. Please try again later."
            + str(e)
        )
