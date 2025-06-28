from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.responses import ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.start_settings.update_start_settings import update_start_settings
from app.modules.start_settings.get_start_settings import get_start_settings
from app.modules.start_settings.start_settings_types import (
    StartSettings,
    StartSettingsRequest,
)


router = APIRouter(tags=["Start Settings"], prefix="/start-settings")


@router.get(
    path="/",
    summary="Get Start Settings for the current user",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response},
)
async def get_get_settings(
    request: Request, user: Annotated[CurrentUser, Depends(auth_user)]
) -> StartSettings:
    """
    Get the Start settings for the user.
    """
    return await get_start_settings(request, user)


@router.put(
    path="/",
    summary="Update Start Settings for the current user",
    status_code=status.HTTP_200_OK,
    responses={
        **ResponseDocs.unauthorized_response,
        **ResponseDocs.not_found_response,
    },
)
async def put_update_settings(
    request: Request,
    body: StartSettingsRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> StartSettings:
    """
    Update the Start Settings for the current user.
    """
    return await update_start_settings(request, body, user)
