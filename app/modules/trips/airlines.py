from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, ListResponse
from app.common.types import AsyncDatabase
from app.modules.flights.flights_types import Airline


async def search_airlines(
    request: Request, iata: str | None, name: str | None
) -> ListResponse[Airline]:
    """
    Search for airlines based on the provided query.
    If both `iata` and `name` are set, IATA code will be prioritized.
    """
    if not iata and not name:
        return ListResponse[Airline](entities=[])

    db: AsyncDatabase = request.app.state.db
    logger = request.app.state.logger

    try:
        query = {}
        if iata:
            query["iata"] = {"$regex": iata, "$options": "i"}
        if name and not iata:
            query["name"] = {"$regex": name, "$options": "i"}

        collection = db.get_collection(DbCollection.AIRLINES)
        results = await collection.find(query).to_list(length=100)

        if not results:
            logger.info(f"No airlines found for query: {query}")
            return ListResponse[Airline](entities=[])

        return ListResponse[Airline](entities=results)

    except Exception as e:
        logger.error(
            f"Error searching airlines for iata '{iata}' and name '{name}': {e}"
        )
        raise InternalServerErrorException("Failed to search airlines: " + str(e))
