from typing_extensions import Annotated
from fastapi import APIRouter, Request, status
from fastapi.params import Depends

from app.modules.activities.activities_types import (
    ActivitiesConfig,
    ChoreRequest,
    GoalsRequest,
)
from app.modules.activities.get_activities import get_activities
from app.common.responses import ResponseDocs
from app.modules.activities.add_chore import add_chore
from app.modules.activities.delete_chore import delete_chore
from app.modules.activities.update_chore import update_chore
from app.modules.activities.update_goals import update_goals
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user


router = APIRouter(tags=["Activities"], prefix="/activities")


@router.get(
    path="/",
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


@router.patch(
    path="/goals",
    summary="Update Activity Goals",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def patch_update_goals(
    request: Request,
    body: GoalsRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
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
    user: Annotated[CurrentUser, Depends(auth_user)],
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
    user: Annotated[CurrentUser, Depends(auth_user)],
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
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> ActivitiesConfig:
    """
    Delete a cycling chore for the current user.
    """
    return await delete_chore(request, id, user)
