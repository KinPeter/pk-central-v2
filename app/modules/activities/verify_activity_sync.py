from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException
from app.modules.activities.activities_types import (
    VerifyActivitySyncRequest,
    VerifyActivitySyncResponse,
)
from app.modules.auth.auth_types import CurrentUser


async def verify_activity_sync(
    request: Request, body: VerifyActivitySyncRequest, user: CurrentUser
) -> VerifyActivitySyncResponse:
    """
    Verify if the Strava activity IDs are already synced for the user.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.ACTIVITIES_SYNC_META)
        sync_meta = await collection.find_one({"user_id": user.id})

        request_data = body.model_dump(
            exclude_none=True, exclude_unset=True, mode="json"
        )
        activity_ids = request_data["activity_ids"]

        if not sync_meta or len(sync_meta["synced_ids"]) == 0:
            return VerifyActivitySyncResponse(unsynced=activity_ids)

        unsynced_ids = [
            activity_id
            for activity_id in activity_ids
            if activity_id not in sync_meta["synced_ids"]
        ]

        return VerifyActivitySyncResponse(unsynced=unsynced_ids)

    except Exception as e:
        logger.error(f"Error verifying unsynced activities for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while verifying unsynced activities." + str(e)
        )
