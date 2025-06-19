from logging import Logger
from fastapi import Request
from app.common.db import DbCollection
from app.common.email import EmailManager
from app.common.environment import PkCentralEnv
from app.common.responses import (
    ConflictException,
    ForbiddenOperationException,
    IdResponse,
    InternalServerErrorException,
)
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import PasswordLoginRequest
from app.modules.auth.auth_utils import get_hashed
from app.modules.auth.user_utils import create_initial_user


async def password_signup(body: PasswordLoginRequest, request: Request) -> IdResponse:
    env: PkCentralEnv = request.app.state.env
    logger: Logger = request.app.state.logger
    db: AsyncDatabase = request.app.state.db
    email_manager = EmailManager(env)
    email = body.email.lower().strip()
    password = body.password.strip()

    is_restricted = env.EMAILS_ALLOWED is not None and env.EMAILS_ALLOWED != "all"
    if is_restricted and email not in env.EMAILS_ALLOWED.split(","):
        raise ForbiddenOperationException("Sign up")

    users_collection = db.get_collection(DbCollection.USERS)
    existing_user = await users_collection.find_one({"email": email})
    if existing_user:
        raise ConflictException("User with this email already exists")

    try:
        user = await create_initial_user(email, db, logger)

        password_hash, password_salt = get_hashed(password)

        await users_collection.update_one(
            {"id": user["id"]},
            {"$set": {"password_hash": password_hash, "password_salt": password_salt}},
        )

        if env.PK_ENV.lower() != "test":
            email_manager.send_signup_notification(email)

        return IdResponse(id=user["id"])

    except Exception as e:
        logger.error(f"Error during password signup {email}: {e}")
        await users_collection.find_one_and_delete({"email": email})
        raise InternalServerErrorException(
            "An error occurred while signing up with password. Please try again later."
            + str(e)
        )
