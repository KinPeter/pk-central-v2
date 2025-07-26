from datetime import datetime
from typing import Any
from fastapi import Request
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException
from app.modules.auth.auth_types import CurrentUser
from app.modules.strava.strava_types import (
    StravaActivityType,
    StravaDbCollection,
    StravaRoutesResponse,
)
from app.modules.strava.strava_utils import generate_routemap


async def create_routemap(
    request: Request,
    user: CurrentUser,
    before: datetime | None,
    after: datetime | None,
    types: list[StravaActivityType] | None = None,
) -> StravaRoutesResponse:
    env: PkCentralEnv = request.app.state.env
    logger = request.app.state.logger
    db_client = AsyncMongoClient(
        host=env.STRAVA_DB_URI, connectTimeoutMS=5000, server_api=ServerApi("1")
    )
    try:
        await db_client.admin.command("ping")
    except Exception as e:
        logger.error(f"Error connecting to Strava database: {e}")
        raise InternalServerErrorException(
            detail="Failed to connect to Strava database. " + str(e)
        )

    try:
        db = db_client.get_database("strava")
        activities_collection = db.get_collection(StravaDbCollection.ACTIVITIES)

        if not types:
            types = [
                StravaActivityType.WALK,
                StravaActivityType.RUN,
                StravaActivityType.RIDE,
            ]

        filter_query: dict[str, Any] = {"user_id": user.id}

        filter_query["type"] = {
            "$in": [t.value if hasattr(t, "value") else t for t in types]
        }

        date_filter = {}
        if after:
            date_filter["$gte"] = after
        if before:
            date_filter["$lte"] = before
        if date_filter:
            filter_query["start_date"] = date_filter

        logger.info(
            f"Fetching routes for user: {user.id} with filters {str(filter_query)}"
        )
        routes = await activities_collection.find(filter_query).to_list()

        if not routes:
            logger.info(f"No routes found for user {user.id}")
            return StravaRoutesResponse(
                routemap=None,
                after=after.isoformat() if after else None,
                before=before.isoformat() if before else None,
                types=[],
                activity_count=0,
            )

        logger.info(
            f"Found {len(routes)} routes for user {user.id}, generating routemap."
        )

        routemap = generate_routemap(activities=routes, logger=logger, sampling_rate=1)

        return StravaRoutesResponse(
            routemap=routemap,
            after=after.isoformat() if after else None,
            before=before.isoformat() if before else None,
            types=list(set(route["type"] for route in routes)),
            activity_count=len(routes),
        )

    except Exception as e:
        logger.error(f"Error creating routemap for user {user.id}: {str(e)}")
        raise InternalServerErrorException(
            detail=f"Could not create routemap: {str(e)}",
        )

    finally:
        await db_client.close()
        logger.info("Strava routemap created, MongoDB connection closed.")
