from logging import Logger
from fastapi import Request
from app.common.db import DbCollection
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, UnauthorizedException
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import LoginResponse, PasswordLoginRequest
from app.modules.auth.auth_utils import get_access_token, verify_password


async def password_login(body: PasswordLoginRequest, request: Request) -> LoginResponse:
    """
    Log in a user with email and password.
    If the user does not exist or the password is incorrect, it will return an error.
    """
    env: PkCentralEnv = request.app.state.env
    logger: Logger = request.app.state.logger
    db: AsyncDatabase = request.app.state.db
    email = body.email.lower().strip()
    password = body.password.strip()

    try:
        user = await db.get_collection(DbCollection.USERS).find_one({"email": email})
    except Exception as e:
        logger.error(f"Error fetching user {email}: {e}")
        raise InternalServerErrorException(
            "An error occurred while logging in. Please try again later." + str(e)
        )

    if not user or not verify_password(
        raw_password=password,
        hashed_password=user["password_hash"],
        salt=user["password_salt"],
    ):
        raise UnauthorizedException("Invalid email or password")

    try:
        token, expires_at = get_access_token(
            user_id=user["id"], secret=env.JWT_SECRET, expires_in_days=env.TOKEN_EXPIRY
        )

        return LoginResponse(
            email=email, id=user["id"], token=token, expires_at=expires_at
        )

    except Exception as e:
        logger.error(f"Error logging in user {email}: {e}")
        raise InternalServerErrorException(
            "An error occurred while logging in. Please try again later." + str(e)
        )
