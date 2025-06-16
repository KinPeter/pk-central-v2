from fastapi import APIRouter, Request
from fastapi.params import Body

from app.common.responses import MessageResponse
from app.modules.auth.auth_types import EmailLoginRequest
from app.modules.auth.request_login_code import request_login_code


router = APIRouter(tags=["Auth"], prefix="/auth")


@router.post(path="/login-code", summary="Request Login Code")
async def post_request_login_code(
    body: EmailLoginRequest, request: Request
) -> MessageResponse:
    """
    Request a login code to be sent to the user's email.
    If the user does not have an account, a new account will be created.
    """
    return await request_login_code(body, request)
