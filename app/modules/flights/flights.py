from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.crud_handler import CrudHandler
from app.common.db import DbCollection
from app.common.responses import IdResponse, ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.flights.flights_types import Flight, FlightRequest
from app.modules.flights.flights_utils import to_flight
from app.modules.flights.get_flights import get_flights


router = APIRouter(tags=["Flights"], prefix="/flights")


@router.get(
    path="/",
    summary="Get Flights",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_flights(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
    is_planned: bool | None = None,
) -> ListResponse[Flight]:
    """
    Get all flights for the user.
    If `is_planned` is provided, filter flights by planned status.
    If not provided, return all flights.
    """
    return await get_flights(
        request=request,
        user=user,
        is_planned=is_planned,
    )


@router.post(
    path="/",
    summary="Create Flight",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_create_flight(
    request: Request,
    body: FlightRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Flight:
    """
    Create a new flight for the user.
    """
    return await CrudHandler[Flight](
        request=request,
        user=user,
        collection_name=DbCollection.FLIGHTS,
        entity_name="Flight",
    ).create(body, mapper_fn=to_flight)


@router.put(
    path="/{id}",
    summary="Update Flight",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_flight(
    request: Request,
    id: str,
    body: FlightRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> Flight:
    """
    Update an existing flight for the user.
    """
    return await CrudHandler[Flight](
        request=request,
        user=user,
        collection_name=DbCollection.FLIGHTS,
        entity_name="Flight",
    ).update(id, body, mapper_fn=to_flight)


@router.delete(
    path="/{id}",
    summary="Delete Flight",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def delete_delete_flight(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> IdResponse:
    """
    Delete a flight for the user.
    """
    return await CrudHandler[Flight](
        request=request,
        user=user,
        collection_name=DbCollection.FLIGHTS,
        entity_name="Flight",
    ).delete(id)
