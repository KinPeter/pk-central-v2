import base64
import hashlib
import jwt
import os
import random
import secrets
import time
from datetime import datetime, timedelta, timezone
from logging import Logger
from fastapi import Header, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import Annotated

from app.common.db import DbCollection
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, UnauthorizedException
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import CurrentUser


def get_access_token(
    user_id: str, secret: str, expires_in_days: int | str
) -> tuple[str, datetime]:
    expires_in_seconds = int(expires_in_days) * 24 * 60 * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
    payload = {
        "user_id": user_id,
        "exp": int(time.time()) + expires_in_seconds,
    }
    token = jwt.encode(payload, key=secret, algorithm="HS256")
    return token, expires_at


def verify_token(token: str, secret: str) -> str:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(reason="Token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException(reason="Invalid token")
    except Exception as e:
        raise UnauthorizedException(reason=f"Token verification failed: {str(e)}")


class LoginCodeData(BaseModel):
    login_code: str
    hashed_login_code: str
    salt: str
    expiry: datetime


def get_login_code(expires_in_minutes: int | str) -> LoginCodeData:
    code = str(random.randint(100000, 999999))
    hashed, salt = get_hashed(code)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=int(expires_in_minutes))
    return LoginCodeData(
        login_code=code, hashed_login_code=hashed, salt=salt, expiry=expiry
    )


def get_hashed(raw_string: str) -> tuple[str, str]:
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", raw_string.encode("utf-8"), salt, 100_000
    )
    hash_b64 = base64.b64encode(hash_bytes).decode("utf-8")
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    return hash_b64, salt_b64


def verify_login_code(
    raw_code: str, hashed_code: str, salt: str, expiry: datetime
) -> bool:
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expiry:
        raise UnauthorizedException(reason="Login code has expired")

    salt_bytes = base64.b64decode(salt.encode("utf-8"))
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", raw_code.encode("utf-8"), salt_bytes, 100_000
    )
    hash_b64 = base64.b64encode(hash_bytes).decode("utf-8")
    if hash_b64 != hashed_code:
        raise UnauthorizedException(reason="Invalid login code")
    return True


def generate_api_key_data() -> tuple[str, str]:
    random_part = secrets.token_urlsafe(32)
    raw_key = f"pk_{random_part}"
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, hashed_key


def verify_password(raw_password: str, hashed_password: str, salt: str) -> bool:
    salt_bytes = base64.b64decode(salt.encode("utf-8"))
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", raw_password.encode("utf-8"), salt_bytes, 100_000
    )
    hash_b64 = base64.b64encode(hash_bytes).decode("utf-8")
    if hash_b64 != hashed_password:
        raise UnauthorizedException(reason="Invalid password")
    return True


async def _get_user_by_id(
    user_id: str, db: AsyncDatabase, logger: Logger
) -> CurrentUser:
    try:
        user = await db.get_collection(DbCollection.USERS).find_one({"id": user_id})
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise InternalServerErrorException(detail="Failed to fetch user data" + str(e))

    if not user:
        raise UnauthorizedException(reason="Invalid token")

    return CurrentUser(id=user_id, email=user["email"])


async def auth_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Security(HTTPBearer())],
) -> CurrentUser:
    """
    Authenticate the user based on the provided JWT bearer token.
    Used as a dependency in routes that require authentication.
    """
    db: AsyncDatabase = request.app.state.db
    logger: Logger = request.app.state.logger
    env: PkCentralEnv = request.app.state.env

    user_id: str = verify_token(credentials.credentials, env.JWT_SECRET)
    return await _get_user_by_id(user_id, db, logger)


async def auth_api_key(
    request: Request,
    api_key: Annotated[str, Header(alias="X-PK-Api-Key")],
) -> CurrentUser:
    """
    Authenticate the user based on the X-PK-Api-Key request header.
    Used as a dependency in routes that accept API key authentication only.
    """
    db: AsyncDatabase = request.app.state.db
    logger: Logger = request.app.state.logger

    hashed = hashlib.sha256(api_key.encode()).hexdigest()

    try:
        doc = await db.get_collection(DbCollection.API_KEYS).find_one(
            {"hashed_key": hashed}
        )
    except Exception as e:
        logger.error(f"Error looking up API key: {e}")
        raise InternalServerErrorException(detail="Failed to validate API key")

    if not doc:
        raise UnauthorizedException(reason="Invalid API key")

    try:
        await db.get_collection(DbCollection.API_KEYS).update_one(
            {"hashed_key": hashed},
            {"$set": {"last_used_at": datetime.now(timezone.utc).isoformat()}},
        )
    except Exception as e:
        logger.error(f"Error updating last_used_at for API key {doc['id']}: {e}")

    return await _get_user_by_id(doc["user_id"], db, logger)


async def auth_user_or_api_key(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(HTTPBearer(auto_error=False)),
    ] = None,
    api_key: Annotated[str | None, Header(alias="X-PK-Api-Key")] = None,
) -> CurrentUser:
    """
    Authenticate the user via either a JWT bearer token or X-PK-Api-Key header.
    API key takes priority when both are provided.
    Used as a dependency in routes that accept either authentication method.
    """
    if api_key:
        return await auth_api_key(request, api_key)

    if credentials:
        db: AsyncDatabase = request.app.state.db
        logger: Logger = request.app.state.logger
        env: PkCentralEnv = request.app.state.env
        user_id: str = verify_token(credentials.credentials, env.JWT_SECRET)
        return await _get_user_by_id(user_id, db, logger)

    raise UnauthorizedException(reason="Authentication required")
