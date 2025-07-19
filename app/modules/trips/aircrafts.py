from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, ListResponse
from app.modules.flights.flights_types import Aircraft


async def search_aircrafts(request: Request, query: str) -> ListResponse[Aircraft]:
    """
    Search for aircrafts based on the provided query.
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.AIRCRAFTS)
        results = await collection.find(
            {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"icao": {"$regex": query, "$options": "i"}},
                ]
            }
        ).to_list(length=100)

        if not results:
            logger.info(f"No aircrafts found for query: {query}")
            return ListResponse[Aircraft](entities=[])

        return ListResponse[Aircraft](entities=results)

    except Exception as e:
        logger.error(f"Error searching aircrafts for query '{query}': {e}")
        raise InternalServerErrorException("Failed to search aircrafts: " + str(e))
