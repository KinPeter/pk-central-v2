from typing_extensions import Annotated
from fastapi import APIRouter, Depends, Query, status, Request

from app.common.responses import ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.flights.flights_types import Aircraft, Airline
from app.modules.trips.aircrafts import search_aircrafts
from app.modules.trips.airlines import search_airlines
from app.modules.trips.airports import get_airport_data
from app.modules.trips.trips_types import AirportResponse


router = APIRouter(prefix="/trips", tags=["Trips"])


@router.get(
    path="/airports",
    summary="Get airport data by IATA code",
    status_code=status.HTTP_200_OK,
    responses={
        **ResponseDocs.unauthorized_response,
        **ResponseDocs.not_found_response,
    },
)
async def get_get_airport_data(
    request: Request,
    iata: Annotated[
        str, Query(description="IATA code of the airport", pattern=r"^[a-zA-Z]{3}$")
    ],
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> AirportResponse:
    """
    Get airport data based on the provided IATA code.
    """
    return await get_airport_data(request, iata_code=iata)


@router.get(
    path="/aircrafts",
    summary="Search for aircrafts by name or ICAO code",
    status_code=status.HTTP_200_OK,
    responses={
        **ResponseDocs.unauthorized_response,
    },
)
async def get_search_aircrafts(
    request: Request,
    search: Annotated[str, Query(description="Search query for aircrafts")],
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> ListResponse[Aircraft]:
    """
    Search for aircrafts based on the provided query.
    """
    return await search_aircrafts(request, query=search)


@router.get(
    path="/airlines",
    summary="Search for airlines by name or IATA code",
    status_code=status.HTTP_200_OK,
    responses={
        **ResponseDocs.unauthorized_response,
    },
)
async def get_search_airlines(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
    iata: (
        Annotated[
            str | None,
            Query(description="Search by IATA code", pattern=r"^[a-zA-Z0-9]{2}$"),
        ]
        | None
    ) = None,
    name: (
        Annotated[
            str | None,
            Query(description="Search query for airlines by name", min_length=2),
        ]
        | None
    ) = None,
) -> ListResponse[Airline]:
    """
    Search for airlines based on the provided query.
    If both `iata` and `name` are set, IATA code will be prioritized.
    """
    return await search_airlines(request, iata=iata, name=name)
