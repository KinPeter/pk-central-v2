from typing import Annotated
from fastapi import Depends, Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, ListResponse
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.flights.flights_types import Flight
from app.modules.flights.flights_utils import to_flight


async def get_flights(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
    is_planned: bool | None = None,
) -> ListResponse[Flight]:
    """
    Retrieve a list of flights for the user.
    """
    db: AsyncDatabase = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.FLIGHTS)

        query: dict[str, str | bool] = {"user_id": user.id}
        if is_planned is not None:
            query["is_planned"] = is_planned

        data = await collection.find(query).to_list(length=None)
        if not data:
            return ListResponse(entities=[])

        entities = [to_flight(item) for item in data]
        return ListResponse(entities=entities)

    except Exception as e:
        logger.error(f"Error retrieving Flights list for user {user.id}: {e}")
        raise InternalServerErrorException(
            f"An error occurred while retrieving the Flights list: " + str(e)
        )
