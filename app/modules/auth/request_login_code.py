import uuid
from datetime import datetime, timezone
from logging import Logger
from fastapi import Request
from app.common.db import DbCollection
from app.common.email import EmailManager
from app.common.environment import PkCentralEnv
from app.common.responses import (
    ForbiddenOperationException,
    InternalServerErrorException,
    MessageResponse,
)
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import EmailLoginRequest
from app.modules.auth.auth_utils import get_login_code


async def request_login_code(
    body: EmailLoginRequest, request: Request
) -> MessageResponse:
    env: PkCentralEnv = request.app.state.env
    logger: Logger = request.app.state.logger
    db: AsyncDatabase = request.app.state.db
    email_manager = EmailManager(env)
    email = body.email.lower().strip()

    try:
        is_restricted = env.EMAILS_ALLOWED is not None and env.EMAILS_ALLOWED != "all"
        if is_restricted and email not in env.EMAILS_ALLOWED.split(","):
            raise ForbiddenOperationException("Sign up")

        users_collection = db.get_collection(DbCollection.USERS)
        existing_user = await users_collection.find_one({"email": email})

        user = None

        if existing_user:
            user = existing_user
        else:
            user = {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc),
                "email": email,
                "login_code_hash": None,
                "login_code_salt": None,
                "login_code_expires": None,
                "password_hash": None,
                "password_salt": None,
            }
            await users_collection.insert_one(user)
            logger.info(f"New user created with email: {email} (ID: {user['id']})")
            # TODO generate initial settings for the user
            logger.warning("Initial settings generation is not implemented yet.")
            # TODO generate initial activities data for the user
            logger.warning("Initial activities data generation is not implemented yet.")
            email_manager.send_signup_notification(email)

        login_code_data = get_login_code(env.LOGIN_CODE_EXPIRY)

        await users_collection.update_one(
            {"id": user["id"]},
            {
                "$set": {
                    "login_code_hash": login_code_data.hashed_login_code,
                    "login_code_salt": login_code_data.salt,
                    "login_code_expires": login_code_data.expiry,
                }
            },
        )

        email_manager.send_login_code(email, login_code_data.login_code)

        return MessageResponse(message="Check your inbox")

    except Exception as e:
        logger.error(f"Error requesting login code for {email}: {e}")
        raise InternalServerErrorException(
            "An error occurred while requesting the login code. Please try again later."
            + str(e)
        )
