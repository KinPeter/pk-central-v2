from typing_extensions import Annotated
from fastapi import APIRouter, Depends, Query, status, Request
from pydantic import Field

from app.common.constants import YEAR_REGEX
from app.common.responses import ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user_or_api_key
from app.modules.flights.flights_types import Aircraft, Airline
from app.modules.trips.get_trips import get_trips
from app.modules.trips.get_trips_stats import get_trips_stats
from app.modules.trips.get_trips_maps import get_trips_maps
from app.modules.trips.aircrafts import search_aircrafts
from app.modules.trips.airlines import search_airlines
from app.modules.trips.airports import get_airport_data
from app.modules.trips.trips_types import AirportResponse, Trips, TripsStats, TripsStatsRequest, TripsMaps, TripsMapsRequest


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
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
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
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
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
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
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


@router.post(
    path="/stats",
    summary="Get trips stats for the authenticated user",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_trips_stats(
    request: Request,
    body: TripsStatsRequest,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> TripsStats:
    """
    Compute stats for the authenticated user's flights and visits.
    Optionally filter by years or by providing lists of flight or visit IDs.
    """
    return await get_trips_stats(request, user_id=user.id, body=body)


@router.post(
    path="/maps",
    summary="Get trips map data for the authenticated user",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_trips_maps(
    request: Request,
    body: TripsMapsRequest,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> TripsMaps:
    """
    Compute map data for the authenticated user's flights and visits.
    Optionally filter by years or by providing lists of flight or visit IDs.
    """
    return await get_trips_maps(request, user_id=user.id, body=body)


@router.post(
    path="/{user_id}/stats",
    summary="Get trips stats for a user (public)",
    status_code=status.HTTP_200_OK,
)
async def post_user_trips_stats(
    request: Request,
    user_id: str,
    body: TripsStatsRequest,
) -> TripsStats:
    """
    Compute stats for a specific user's flights and visits. No authentication required.
    Optionally filter by years or by providing lists of flight or visit IDs.
    """
    return await get_trips_stats(request, user_id=user_id, body=body)


@router.post(
    path="/{user_id}/maps",
    summary="Get trips map data for a user (public)",
    status_code=status.HTTP_200_OK,
)
async def post_user_trips_maps(
    request: Request,
    user_id: str,
    body: TripsMapsRequest,
) -> TripsMaps:
    """
    Compute map data for a specific user's flights and visits. No authentication required.
    Optionally filter by years or by providing lists of flight or visit IDs.
    """
    return await get_trips_maps(request, user_id=user_id, body=body)


@router.get(
    path="/{user_id}",
    summary="Get trips data for a user",
    status_code=status.HTTP_200_OK,
)
async def get_user_trips(
    request: Request,
    user_id: str,
    year: Annotated[
        list[Annotated[str, Field(pattern=YEAR_REGEX)]] | None,
        Query(description="Filter by year(s), e.g. 2024"),
    ] = None,
) -> Trips:
    """
    Get trips data for a specific user.
    """
    return await get_trips(request, user_id=user_id, year=year)
