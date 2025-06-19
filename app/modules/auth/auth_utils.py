import base64
from datetime import datetime, timedelta, timezone
import hashlib
import os
import time
import jwt
import random

from pydantic import BaseModel

from app.common.responses import UnauthorizedException
from app.modules.auth.auth_types import JWTPayload


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


def verify_token(token: str, secret: str) -> JWTPayload:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(reason="Token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException(reason="Invalid token")


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


def verify_password(raw_password: str, hashed_password: str, salt: str) -> bool:
    salt_bytes = base64.b64decode(salt.encode("utf-8"))
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", raw_password.encode("utf-8"), salt_bytes, 100_000
    )
    hash_b64 = base64.b64encode(hash_bytes).decode("utf-8")
    if hash_b64 != hashed_password:
        raise UnauthorizedException(reason="Invalid password")
    return True
