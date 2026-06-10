from fastapi import Request

from app.common.db import DbCollection
from app.common.date_utils import to_iso_day_start, to_iso_day_end
from app.common.responses import InternalServerErrorException, ListResponse
from app.modules.activities.activities_types import Activity, ActivityQuery
from app.modules.activities.activities_utils import to_activity
from app.modules.auth.auth_types import CurrentUser


async def query_activities(
    request: Request, body: ActivityQuery, user: CurrentUser
) -> ListResponse[Activity]:
    """
    Query activities for the user with optional type and date range filters.
    If no filters are provided, returns all activities sorted by start_date descending.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.ACTIVITIES)

        # Build the filter dict
        filter_dict: dict = {"user_id": user.id}

        if body.types:
            filter_dict["type"] = {"$in": [t.value for t in body.types]}

        if body.from_date or body.to_date:
            date_filter: dict = {}
            if body.from_date:
                date_filter["$gte"] = to_iso_day_start(body.from_date)
            if body.to_date:
                date_filter["$lte"] = to_iso_day_end(body.to_date)
            filter_dict["start_date"] = date_filter

        cursor = collection.find(filter_dict).sort("start_date", -1)
        docs = await cursor.to_list(length=None)

        activities: list[Activity] = [to_activity(doc) for doc in docs]

        logger.info(
            f"Queried {len(activities)} activities for user {user.id}"
            f" (types={body.types}, from={body.from_date}, to={body.to_date})"
        )

        return ListResponse[Activity](entities=activities)

    except Exception as e:
        logger.error(f"Error querying activities for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while querying activities."
        )
