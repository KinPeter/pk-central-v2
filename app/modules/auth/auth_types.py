from datetime import datetime
from pydantic import EmailStr, Field
from app.common.responses import OkResponse
from app.common.types import BaseEntity, PkBaseModel


class User(BaseEntity):
    email: EmailStr
    login_code_hash: str | None
    login_code_salt: str | None
    login_code_expires: datetime | None
    password_hash: str | None
    password_salt: str | None


class CurrentUser(PkBaseModel):
    id: str
    email: str


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
    password: str = Field(..., min_length=6, max_length=128)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "myname@gmail.com",
                    "password": "mysecretpassword",
                }
            ]
        }
    }


class CodeLoginRequest(EmailLoginRequest):
    login_code: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "myname@gmail.com",
                    "login_code": "123456",
                }
            ]
        }
    }


class LoginResponse(OkResponse):
    id: str
    email: str
    token: str
    expires_at: datetime


class LoginCodeResponse(OkResponse):
    login_code: str
