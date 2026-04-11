from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, ListResponse
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import CurrentUser
from app.modules.visits.visits_types import Visit, VisitQuery
from app.modules.visits.visits_utils import to_visit


async def query_visits(
    request: Request,
    user: CurrentUser,
    body: VisitQuery,
) -> ListResponse[Visit]:
    db: AsyncDatabase = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.VISITS)

        query: dict = {"user_id": user.id}
        if body.year:
            query["year"] = {"$in": body.year}
        if body.country:
            query["country"] = {"$in": body.country}

        data = await collection.find(query).to_list(length=None)
        if not data:
            return ListResponse(entities=[])

        entities = [to_visit(item) for item in data]
        return ListResponse(entities=entities)

    except Exception as e:
        logger.error(f"Error querying Visits for user {user.id}: {e}")
        raise InternalServerErrorException(
            f"An error occurred while querying Visits: " + str(e)
        )
