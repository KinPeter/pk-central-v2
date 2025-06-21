from logging import Logger
from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import (
    ForbiddenOperationException,
    IdResponse,
    InternalServerErrorException,
)
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import CurrentUser, PasswordLoginRequest
from app.modules.auth.auth_utils import get_hashed


async def set_password(
    body: PasswordLoginRequest, request: Request, req_user: CurrentUser
) -> IdResponse:
    """
    Set a new password for the user.
    If the user does not exist, it will return an error.
    """
    logger: Logger = request.app.state.logger
    db: AsyncDatabase = request.app.state.db
    email = None

    try:
        email = body.email.lower().strip()
        password = body.password.strip()

        users_collection = db.get_collection(DbCollection.USERS)
        user = await users_collection.find_one({"id": req_user.id})

        if not user or user["email"].lower() != email:
            raise ForbiddenOperationException()

        hashed_password, salt = get_hashed(password)
        await users_collection.update_one(
            {"id": user["id"]},
            {
                "$set": {
                    "password_hash": hashed_password,
                    "password_salt": salt,
                }
            },
        )

        logger.info(f"Password updated successfully for user {email}")
        return IdResponse(id=user["id"])

    except ForbiddenOperationException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating password for user {email}: {e}")
        raise InternalServerErrorException(
            "An error occurred while setting the password. Please try again later."
            + str(e)
        )
