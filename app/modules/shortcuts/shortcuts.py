from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.crud_handler import CrudHandler
from app.common.db import DbCollection
from app.common.responses import IdResponse, ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.shortcuts.shortcuts_types import Shortcut, ShortcutRequest
from app.modules.shortcuts.shortcuts_utils import to_shortcut


router = APIRouter(tags=["Shortcuts"], prefix="/shortcuts")


@router.get(
    path="/",
    summary="Get Shortcuts",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_shortcuts(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> ListResponse[Shortcut]:
    """
    Get all shortcuts for the user.
    """
    return await CrudHandler[Shortcut](
        request=request,
        user=user,
        collection_name=DbCollection.SHORTCUTS,
        entity_name="Shortcut",
    ).get_listed(mapper_fn=to_shortcut)


@router.post(
    path="/",
    summary="Create Shortcut",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_create_shortcut(
    request: Request,
    body: ShortcutRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Shortcut:
    """
    Create a new shortcut for the user.
    """
    return await CrudHandler[Shortcut](
        request=request,
        user=user,
        collection_name=DbCollection.SHORTCUTS,
        entity_name="Shortcut",
    ).create(body, mapper_fn=to_shortcut)


@router.put(
    path="/{id}",
    summary="Update Shortcut",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_shortcut(
    request: Request,
    id: str,
    body: ShortcutRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Shortcut:
    """
    Update an existing shortcut for the user.
    """
    return await CrudHandler[Shortcut](
        request=request,
        user=user,
        collection_name=DbCollection.SHORTCUTS,
        entity_name="Shortcut",
    ).update(id, body, mapper_fn=to_shortcut)


@router.delete(
    path="/{id}",
    summary="Delete Shortcut",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def delete_delete_shortcut(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> IdResponse:
    """
    Delete a shortcut for the user.
    """
    return await CrudHandler[Shortcut](
        request=request,
        user=user,
        collection_name=DbCollection.SHORTCUTS,
        entity_name="Shortcut",
    ).delete(id)
