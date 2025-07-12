from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.crud_handler import CrudHandler
from app.common.db import DbCollection
from app.common.responses import IdResponse, ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.visits.visits_types import Visit, VisitRequest
from app.modules.visits.visits_utils import to_visit


router = APIRouter(tags=["Visits"], prefix="/visits")


@router.get(
    path="/",
    summary="Get Visits",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_visits(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> ListResponse[Visit]:
    """
    Get all visits for the user.
    """
    return await CrudHandler[Visit](
        request=request,
        user=user,
        collection_name=DbCollection.VISITS,
        entity_name="Visit",
    ).get_listed(mapper_fn=to_visit)


@router.post(
    path="/",
    summary="Create Visit",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_create_visit(
    request: Request,
    body: VisitRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Visit:
    """
    Create a new visit for the user.
    """
    return await CrudHandler[Visit](
        request=request,
        user=user,
        collection_name=DbCollection.VISITS,
        entity_name="Visit",
    ).create(body, mapper_fn=to_visit)


@router.put(
    path="/{id}",
    summary="Update Visit",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_visit(
    request: Request,
    id: str,
    body: VisitRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Visit:
    """
    Update an existing visit for the user.
    """
    return await CrudHandler[Visit](
        request=request,
        user=user,
        collection_name=DbCollection.VISITS,
        entity_name="Visit",
    ).update(id, body, mapper_fn=to_visit)


@router.delete(
    path="/{id}",
    summary="Delete Visit",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def delete_delete_visit(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> IdResponse:
    """
    Delete a visit for the user.
    """
    return await CrudHandler[Visit](
        request=request,
        user=user,
        collection_name=DbCollection.VISITS,
        entity_name="Visit",
    ).delete(id)
