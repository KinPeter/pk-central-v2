from typing import Annotated
from fastapi import APIRouter, Request, status
from fastapi.params import Depends

from app.common.responses import IdResponse, MessageResponse, ResponseDocs
from app.modules.auth.token_refresh import token_refresh
from app.modules.auth.auth_types import (
    CodeLoginRequest,
    CurrentUser,
    EmailLoginRequest,
    LoginCodeResponse,
    LoginResponse,
    PasswordLoginRequest,
)
from app.modules.auth.auth_utils import auth_user
from app.modules.auth.instant_login_code import instant_login_code
from app.modules.auth.password_login import password_login
from app.modules.auth.password_signup import password_signup
from app.modules.auth.request_login_code import request_login_code
from app.modules.auth.set_password import set_password
from app.modules.auth.verify_login_code import login_code_verify


router = APIRouter(tags=["Auth"], prefix="/auth")


@router.post(
    path="/login-code",
    summary="Request Login Code for sign up or login",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.forbidden_response},
)
async def post_request_login_code(
    body: EmailLoginRequest, request: Request
) -> MessageResponse:
    """
    Request a login code to be sent to the user's email.
    If the user does not have an account, a new account will be created.
    """
    return await request_login_code(body, request)


@router.post(
    path="/instant-login-code",
    summary="[DEV only] Request instant Login Code",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.forbidden_response},
)
async def post_instant_login_code(
    body: EmailLoginRequest, request: Request
) -> LoginCodeResponse:
    """
    Request an login code directly in the response.
    If the user does not have an account, a new account will be created.
    This endpoint is only available in the development environment.
    """
    return await instant_login_code(body, request)


@router.post(
    path="/verify-login-code",
    summary="Log in with a login code",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.forbidden_response},
)
async def post_verify_login_code(
    body: CodeLoginRequest, request: Request
) -> LoginResponse:
    """
    Log in a user with a code sent to their email.
    If the user does not exist or the password is incorrect, it will return an error.
    """
    return await login_code_verify(body, request)


@router.post(
    path="/password-signup",
    summary="Sign up with password",
    status_code=status.HTTP_201_CREATED,
    responses={
        **ResponseDocs.unauthorized_response,
        **ResponseDocs.conflict_response,
        **ResponseDocs.forbidden_response,
    },
)
async def post_password_signup(
    body: PasswordLoginRequest, request: Request
) -> IdResponse:
    """
    Sign up a new user with email and password.
    If the user already exists, it will return a conflict error.
    """
    return await password_signup(body, request)


@router.post(
    path="/password-login",
    summary="Log in with email and password",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_password_login(
    body: PasswordLoginRequest, request: Request
) -> LoginResponse:
    """
    Log in a user with email and password.
    If the user does not exist or the password is incorrect, it will return an error.
    """
    return await password_login(body, request)


@router.post(
    path="/token-refresh",
    summary="Refresh the access token",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_token_refresh(
    request: Request, user: Annotated[CurrentUser, Depends(auth_user)]
) -> LoginResponse:
    """
    Refresh the access token for the current user.
    This endpoint should be called when the access token is about to expire.
    """
    return await token_refresh(request, user)


@router.post(
    path="/set-password",
    summary="Set a new password for the user",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.forbidden_response},
)
async def post_set_password(
    body: PasswordLoginRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> IdResponse:
    """
    Set a new password for the user.
    This works for setting a password for the first time or updating an existing password.
    """
    return await set_password(body, request, user)
