from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.crud_handler import CrudHandler
from app.common.db import DbCollection
from app.common.responses import IdResponse, ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.notes.notes_types import Note, NoteRequest
from app.modules.notes.notes_utils import to_note


router = APIRouter(tags=["Notes"], prefix="/notes")


@router.get(
    path="/",
    summary="Get Notes",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_notes(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> ListResponse[Note]:
    """
    Get all notes for the user.
    """
    return await CrudHandler[Note](
        request=request,
        user=user,
        collection_name=DbCollection.NOTES,
        entity_name="Note",
    ).get_listed(mapper_fn=to_note)


@router.post(
    path="/",
    summary="Create Note",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_create_note(
    request: Request,
    body: NoteRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Note:
    """
    Create a new note for the user.
    """
    return await CrudHandler[Note](
        request=request,
        user=user,
        collection_name=DbCollection.NOTES,
        entity_name="Note",
    ).create(body, mapper_fn=to_note, create_timestamp=True)


@router.put(
    path="/{id}",
    summary="Update Note",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_note(
    request: Request,
    id: str,
    body: NoteRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Note:
    """
    Update an existing note for the user.
    """
    return await CrudHandler[Note](
        request=request,
        user=user,
        collection_name=DbCollection.NOTES,
        entity_name="Note",
    ).update(id, body, mapper_fn=to_note)


@router.delete(
    path="/{id}",
    summary="Delete Note",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def delete_delete_note(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> IdResponse:
    """
    Delete a note for the user.
    """
    return await CrudHandler[Note](
        request=request,
        user=user,
        collection_name=DbCollection.NOTES,
        entity_name="Note",
    ).delete(id)
