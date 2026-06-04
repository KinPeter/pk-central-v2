from typing_extensions import Annotated
from fastapi import APIRouter, Query, Request, status
from fastapi.params import Depends

from app.common.responses import ListResponse, ResponseDocs
from app.modules.activities.activities_types import (
    ActivitiesConfig,
    ChoreRequest,
    GoalsRequest,
    StepsItem,
    StepsSyncResponse,
)
from app.modules.activities.get_activities_config import get_activities_config
from app.modules.activities.get_steps import get_steps
from app.modules.activities.add_chore import add_chore
from app.modules.activities.delete_chore import delete_chore
from app.modules.activities.sync_steps import sync_steps
from app.modules.activities.update_chore import update_chore
from app.modules.activities.update_goals import update_goals
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user_or_api_key

router = APIRouter(tags=["Activities"], prefix="/activities")


@router.get(
    path="/",
    summary="[DEPRECATED] Get Activities Config",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_activities(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> ActivitiesConfig:
    """
    Get the Activities config for the user.
    """
    return await get_activities_config(request, user)


@router.get(
    path="/config",
    summary="Get Activities Config",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_activities_config(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> ActivitiesConfig:
    """
    Get the Activities config for the user.
    """
    return await get_activities_config(request, user)


@router.patch(
    path="/goals",
    summary="Update Activity Goals",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def patch_update_goals(
    request: Request,
    body: GoalsRequest,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> ActivitiesConfig:
    """
    Update the activity goals for the current user.
    """
    return await update_goals(request, body, user)


@router.post(
    path="/chores",
    summary="Add a Cycling Chore",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def post_add_chore(
    request: Request,
    body: ChoreRequest,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> ActivitiesConfig:
    """
    Add a new cycling chore for the current user.
    """
    return await add_chore(request, body, user)


@router.put(
    path="/chores/{id}",
    summary="Update a Cycling Chore",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_chore(
    request: Request,
    id: str,
    body: ChoreRequest,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> ActivitiesConfig:
    """
    Update an existing cycling chore for the current user.
    """
    return await update_chore(request, id, body, user)


@router.delete(
    path="/chores/{id}",
    summary="Delete a Cycling Chore",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def delete_delete_chore(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> ActivitiesConfig:
    """
    Delete a cycling chore for the current user.
    """
    return await delete_chore(request, id, user)


@router.post(
    path="/steps/sync",
    status_code=status.HTTP_200_OK,
    summary="Sync steps from Samsung Health for the user",
    responses={**ResponseDocs.unauthorized_response},
)
async def post_sync_steps(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> StepsSyncResponse:
    """
    Sync steps from Samsung Health for the current user.
    """
    return await sync_steps(request=request, user=user)


@router.get(
    path="/steps",
    summary="Get Steps for User",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response},
)
async def get_get_steps(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
) -> ListResponse[StepsItem]:
    """
    Get steps for the current user within an optional date range.
    Days without steps data are filled with a steps count of 0.
    """
    return await get_steps(request, user, from_date, to_date)
