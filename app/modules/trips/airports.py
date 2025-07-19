from fastapi import Request

from app.common.db import DbCollection
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.ai.gemini_api import GeminiApi
from app.modules.ai.prompts import airport_data_prompt
from app.modules.trips.trips_types import AirportResponse


async def get_airport_data(request: Request, iata_code: str) -> AirportResponse:
    """
    Fetch airport data based on the provided IATA code.
    """
    db = request.app.state.db
    env: PkCentralEnv = request.app.state.env
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.AIRPORTS)
        airport_data = await collection.find_one({"iata": iata_code.upper()})

        if airport_data:
            return AirportResponse(**airport_data)

        gemini_api = GeminiApi(api_key=env.GEMINI_API_KEY, logger=logger)

        response = await gemini_api.generate_json(
            prompt=airport_data_prompt(iata_code.upper())
        )
        if (
            not response.get("iata") == iata_code.upper()
            or not response.get("icao")
            or not response.get("name")
            or not response.get("city")
            or not response.get("country")
            or not response.get("lat")
            or not response.get("lng")
        ):
            logger.error(
                f"Incomplete airport data received for {iata_code}: {response}"
            )
            raise NotFoundException("Airport data")

        return AirportResponse(**response)

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching airport data for {iata_code}: {e}")
        raise InternalServerErrorException("Failed to retrieve airport data: " + str(e))
