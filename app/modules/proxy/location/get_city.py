from fastapi import Request

from app.common.country_data import CountryData
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.proxy.location.location_iq_api import LocationIqApi
from app.modules.proxy.location.location_types import CityLocation


async def get_city(request: Request, lat: float, lng: float) -> CityLocation:
    """
    Get city information based on latitude and longitude.
    """
    env: PkCentralEnv = request.app.state.env
    reverse_url = env.PROXY_LOCATION_REVERSE_URL
    api_key = env.LOCATION_IQ_API_KEY
    logger = request.app.state.logger

    try:
        location_api = LocationIqApi(api_key=api_key, reverse_url=reverse_url)
        location_response = await location_api.reverse_geocode(lat=lat, lon=lng)

        if "address" not in location_response:
            logger.error(f"Address not found for coordinates: {lat}, {lng}")
            raise NotFoundException("Location")

        address = location_response["address"]
        city = (
            address.get("city", "")
            or address.get("town", "")
            or address.get("village", "")
        )
        country_code = address.get("country_code", "")

        countries = CountryData()
        country = countries.get_name(country_code)

        return CityLocation(lat=lat, lng=lng, city=city, country=country)

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get city location: {e}")
        raise InternalServerErrorException("Failed to retrieve city location:" + str(e))
