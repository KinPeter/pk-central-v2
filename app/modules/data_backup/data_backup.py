from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.responses import MessageResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.data_backup.email_backup import email_backup

router = APIRouter(prefix="/data-backup", tags=["Data Backup"])


@router.get(
    "/email",
    summary="Send data backup via email",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response},
)
async def get_email_backup(
    request: Request, user: Annotated[CurrentUser, Depends(auth_user)]
) -> MessageResponse:
    """
    Endpoint to send a data backup email to the user.
    """
    return await email_backup(request, user)
