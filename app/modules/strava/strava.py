from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, status

from app.common.responses import ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.strava.create_routemap import create_routemap
from app.modules.strava.strava_types import (
    StravaActivityType,
    StravaRoutesResponse,
    StravaSyncResponse,
)
from app.modules.strava.sync_routes import sync_strava_routes


router = APIRouter(prefix="/strava", tags=["Strava"])


@router.post(
    path="/routes/sync",
    status_code=status.HTTP_200_OK,
    summary="Sync Strava activities with routes for the user",
    responses={**ResponseDocs.unauthorized_response},
)
async def post_sync_strava_routes(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
    strava_token: Annotated[str, Query(description="Strava access token")],
    force: Annotated[
        bool | None, Query(description="Force sync all activities")
    ] = False,
) -> StravaSyncResponse:
    """
    Sync Strava activities with routes lat/lng data for the current user.
    If `force` is True, it will force a sync for all activities even if the last sync was recent.
    """
    return await sync_strava_routes(
        request=request, user=user, strava_token=strava_token, force=force
    )


@router.get(
    path="/routes/routemap",
    summary="Get routemap coordinates for the user",
    responses={**ResponseDocs.unauthorized_response},
)
async def get_create_routemap(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
    after: Annotated[
        datetime | None,
        Query(
            description="Filter activities after this date - ISO 8601 format, e.g., '2023-10-01T00:00:00Z'",
        ),
    ] = None,
    before: Annotated[
        datetime | None,
        Query(
            description="Filter activities before this date - ISO 8601 format, e.g., '2023-10-01T00:00:00Z'",
        ),
    ] = None,
    types: Annotated[
        list[StravaActivityType] | None,
        Query(
            description="Filter activities by type ('Walk', 'Run', 'Ride'). If not provided, all types are included.",
        ),
    ] = None,
) -> StravaRoutesResponse:
    """
    This endpoint retrieves the routemap coordinates for the current user. You can filter the results by date range and activity type.
    """
    return await create_routemap(
        request=request, user=user, before=before, after=after, types=types
    )
