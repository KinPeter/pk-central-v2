from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.crud_handler import CrudHandler
from app.common.db import DbCollection
from app.common.responses import IdResponse, ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.personal_data.personal_data_types import (
    PersonalData,
    PersonalDataRequest,
)
from app.modules.personal_data.personal_data_utils import to_personal_data


router = APIRouter(tags=["Personal Data"], prefix="/personal-data")


@router.get(
    path="/",
    summary="Get all personal data for the user",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_personal_datas(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> ListResponse[PersonalData]:
    """
    Get all personal data for the user.
    """
    return await CrudHandler[PersonalData](
        request=request,
        user=user,
        collection_name=DbCollection.PERSONAL_DATA,
        entity_name="PersonalData",
    ).get_listed(mapper_fn=to_personal_data)


@router.post(
    path="/",
    summary="Create a new personal data",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_create_personal_data(
    request: Request,
    body: PersonalDataRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> PersonalData:
    """
    Create a new personal data for the user.
    """
    return await CrudHandler[PersonalData](
        request=request,
        user=user,
        collection_name=DbCollection.PERSONAL_DATA,
        entity_name="PersonalData",
    ).create(body, mapper_fn=to_personal_data)


@router.put(
    path="/{id}",
    summary="Update a personal data",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_personal_data(
    request: Request,
    id: str,
    body: PersonalDataRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> PersonalData:
    """
    Update an existing personal data for the user.
    """
    return await CrudHandler[PersonalData](
        request=request,
        user=user,
        collection_name=DbCollection.PERSONAL_DATA,
        entity_name="PersonalData",
    ).update(id, body, mapper_fn=to_personal_data)


@router.delete(
    path="/{id}",
    summary="Delete a personal data",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def delete_delete_personal_data(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> IdResponse:
    """
    Delete a personal data for the user.
    """
    return await CrudHandler[PersonalData](
        request=request,
        user=user,
        collection_name=DbCollection.PERSONAL_DATA,
        entity_name="PersonalData",
    ).delete(id)
