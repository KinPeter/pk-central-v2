from typing_extensions import Annotated
from fastapi import APIRouter, Request, status
from fastapi.params import Depends

from app.modules.activities.activities_types import ActivitiesConfig
from app.modules.activities.get_activities import get_activities
from app.common.responses import ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user


router = APIRouter(tags=["Activities"], prefix="/activities")


@router.get(
    "/",
    summary="Get Activities Config",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_activities(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> ActivitiesConfig:
    """
    Get the Activities config for the user.
    """
    return await get_activities(request, user)
