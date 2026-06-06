from datetime import datetime, timezone
import uuid

from fastapi import Request, UploadFile

from app.common.db import DbCollection
from app.common.responses import (
    ConflictException,
    IdResponse,
    InternalServerErrorException,
    UnprocessableEntityException,
)
from app.modules.activities.activities_types import ActivityType
from app.modules.activities.gpx_utils import parse_strava_gpx
from app.modules.auth.auth_types import CurrentUser

"""
Example curl command to upload a GPX file:

curl -s -w "\nStatus: %{http_code}\n" \
    -X POST "http://localhost:5500/central/v2/activities/upload" \
    -H "x-pk-api-key: <API_KEY>" \
    -H 'accept: application/json' \
    -H 'Content-Type: multipart/form-data' \
    -F "gpx_file=@.temp/Afternoon_Walk.gpx" \
    -F "source_id=1234567890"
"""


async def upload_activity(
    request: Request, user: CurrentUser, gpx_file: UploadFile, source_id: str
) -> IdResponse:
    """
    Upload an activity by parsing data from the GPX file
    """
    if not source_id.strip():
        raise UnprocessableEntityException(detail="source_id must not be empty")

    if (
        not gpx_file
        or not gpx_file.filename
        or not gpx_file.filename.lower().endswith(".gpx")
    ):
        raise UnprocessableEntityException(detail="File must be a GPX file")

    contents = await gpx_file.read()
    decoded = contents.decode("utf-8").strip()

    if not (decoded.startswith("<?xml") and decoded.endswith("</gpx>")):
        raise UnprocessableEntityException(
            detail="File does not appear to be a valid GPX file"
        )

    db = request.app.state.db
    logger = request.app.state.logger

    try:
        activity_data = parse_strava_gpx(decoded, source_id)
        activities_collection = db.get_collection(DbCollection.ACTIVITIES)
        sync_meta_collection = db.get_collection(DbCollection.ACTIVITIES_SYNC_META)
        user_sync_data = await sync_meta_collection.find_one({"user_id": user.id})

        logger.info(activity_data)

        if not user_sync_data:
            logger.info(
                f"No sync metadata found for user {user.id}, creating new entry."
            )
            user_sync_data = {
                "user_id": user.id,
                "synced_ids": [],
                "current_bike_kms": 0,
                "last_synced": None,
            }
            await sync_meta_collection.insert_one(user_sync_data)

        if source_id in user_sync_data["synced_ids"]:
            logger.info(f"Activity {source_id} already synced, skipping.")
            raise ConflictException(detail=f"Activity already synced: {source_id}")

        activity_dto = activity_data.model_dump(mode="json")
        activity_dto["id"] = str(uuid.uuid4())
        activity_dto["user_id"] = user.id

        await activities_collection.insert_one(activity_dto)

        user_sync_data["synced_ids"].append(source_id)
        user_sync_data["last_synced"] = datetime.now(timezone.utc).isoformat()

        if activity_data.type == ActivityType.RIDE:
            user_sync_data["current_bike_kms"] = round(
                user_sync_data["current_bike_kms"] + activity_data.distance / 1000,
                1,
            )

        await sync_meta_collection.update_one(
            {"user_id": user.id},
            {"$set": user_sync_data},
        )
        logger.info(f"Uploaded activity {source_id} for user {user.id}")

        return IdResponse(id=activity_dto["id"])

    except ValueError as e:
        logger.error(f"Error parsing GPX file: {e}")
        raise UnprocessableEntityException(detail=str(e))
    except ConflictException as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading activity for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while uploading the activity." + str(e)
        )
