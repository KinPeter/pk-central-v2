from fastapi import Request, UploadFile

from app.common.db import DbCollection
from app.common.responses import (
    IdResponse,
    InternalServerErrorException,
    UnprocessableEntityException,
)
from app.modules.activities.gpx_utils import parse_strava_gpx
from app.modules.auth.auth_types import CurrentUser

"""
Example curl command to upload a GPX file:

curl -s -w "\nStatus: %{http_code}\n" \
    -X POST "http://localhost:5500/central/v2/activities/upload" \
    -H "x-pk-api-key: <API_KEY>" \
    -F "gpx_file=@.temp/Afternoon_Walk.gpx" \
    -F "source_id=1234567890"
"""


async def upload_activity(
    request: Request, user: CurrentUser, gpx_file: UploadFile, source_id: str
) -> IdResponse:
    """
    Upload an activity by parsing data from the GPX file
    """
    # Validation
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
        sync_meta = await sync_meta_collection.find_one({"user_id": user.id})

        logger.info(activity_data)

        return IdResponse(id="")

    except Exception as e:
        logger.error(f"Error uploading activity for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while uploading the activity." + str(e)
        )
