from datetime import datetime, timezone

from fastapi import HTTPException, Request, status

from app.common.date_utils import add_one_day, subtract_days
from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, ListResponse
from app.modules.activities.activities_types import StepsItem
from app.modules.auth.auth_types import CurrentUser


async def get_steps(
    request: Request,
    user: CurrentUser,
    from_date: str | None,
    to_date: str | None,
) -> ListResponse[StepsItem]:
    """
    Get steps for the user within an optional date range.
    If no dates are provided, defaults to the last 30 days.
    Days without steps data are filled with a steps count of 0.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = subtract_days(today, 1)

        if to_date is None:
            to_date = yesterday

        if from_date is None:
            from_date = subtract_days(to_date, 29)

        # Validate date format
        try:
            datetime.strptime(from_date, "%Y-%m-%d")
            datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid date format. Use YYYY-MM-DD.",
            )

        # Validate range
        if from_date > to_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="'from' date must be before or equal to 'to' date.",
            )

        collection = db.get_collection(DbCollection.STEPS)
        cursor = collection.find(
            {"user_id": user.id, "date": {"$gte": from_date, "$lte": to_date}}
        )
        steps_docs = await cursor.to_list(length=None)

        # Build a map of date -> steps from DB results
        steps_map: dict[str, int] = {}
        for doc in steps_docs:
            steps_map[doc["date"]] = doc["steps"]

        # Generate the complete list of days, zero-filling missing entries
        items: list[StepsItem] = []
        current = from_date
        while current <= to_date:
            items.append(StepsItem(steps=steps_map.get(current, 0), date=current))
            current = add_one_day(current)

        logger.info(
            f"Retrieved {len(steps_docs)} step records for user {user.id} "
            f"from {from_date} to {to_date}, returning {len(items)} days"
        )

        return ListResponse[StepsItem](entities=items)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving steps for user {user.id}: {e}")
        raise InternalServerErrorException("An error occurred while retrieving steps.")
