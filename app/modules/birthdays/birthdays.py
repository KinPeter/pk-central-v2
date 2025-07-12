from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.crud_handler import CrudHandler
from app.common.db import DbCollection
from app.common.responses import IdResponse, ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.birthdays.birthdays_types import Birthday, BirthdayRequest
from app.modules.birthdays.birthdays_utils import to_birthday


router = APIRouter(tags=["Birthdays"], prefix="/birthdays")


@router.get(
    path="/",
    summary="Get Birthdays",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_birthdays(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> ListResponse[Birthday]:
    """
    Get all birthdays for the user.
    """
    return await CrudHandler[Birthday](
        request=request,
        user=user,
        collection_name=DbCollection.BIRTHDAYS,
        entity_name="Birthday",
    ).get_listed(mapper_fn=to_birthday)


@router.post(
    path="/",
    summary="Create Birthday",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_create_birthday(
    request: Request,
    body: BirthdayRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Birthday:
    """
    Create a new birthday for the user.
    """
    return await CrudHandler[Birthday](
        request=request,
        user=user,
        collection_name=DbCollection.BIRTHDAYS,
        entity_name="Birthday",
    ).create(body, mapper_fn=to_birthday)


@router.put(
    path="/{id}",
    summary="Update Birthday",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_birthday(
    request: Request,
    id: str,
    body: BirthdayRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Birthday:
    """
    Update an existing birthday for the user.
    """
    return await CrudHandler[Birthday](
        request=request,
        user=user,
        collection_name=DbCollection.BIRTHDAYS,
        entity_name="Birthday",
    ).update(id, body, mapper_fn=to_birthday)


@router.delete(
    path="/{id}",
    summary="Delete Birthday",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def delete_delete_birthday(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> IdResponse:
    """
    Delete a birthday for the user.
    """
    return await CrudHandler[Birthday](
        request=request,
        user=user,
        collection_name=DbCollection.BIRTHDAYS,
        entity_name="Birthday",
    ).delete(id)
