from datetime import datetime
from pydantic import EmailStr
from app.common.types import BaseEntity, PkBaseModel


class User(BaseEntity):
    email: EmailStr
    login_code_hash: str | None
    login_code_salt: str | None
    login_code_expires: datetime | None
    password_hash: str | None
    password_salt: str | None


class JWTPayload:
    user_id: str
    exp: int


class EmailLoginRequest(PkBaseModel):
    email: EmailStr

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "myname@gmail.com",
                }
            ]
        }
    }


class PasswordLoginRequest(EmailLoginRequest):
    password: str


class CodeLoginRequest(EmailLoginRequest):
    login_code: str


class LoginResponse(PkBaseModel):
    id: str
    email: str
    token: str
    expires_at: datetime
