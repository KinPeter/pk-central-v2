from fastapi import Request

from app.common.db import DbCollection
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.auth.auth_types import CurrentUser
from app.modules.start_settings.start_settings_types import StartSettings


async def get_start_settings(request: Request, user: CurrentUser) -> StartSettings:
    """
    Get the Start settings for the user.
    """
    db = request.app.state.db
    logger = request.app.state.logger
    env: PkCentralEnv = request.app.state.env

    try:
        collection = db.get_collection(DbCollection.START_SETTINGS)
        data = await collection.find_one({"user_id": user.id})

        if not data:
            logger.error(f"Start Settings not found for user {user.id}")
            raise NotFoundException(resource="Start Settings")

        return StartSettings(
            id=data["id"],
            created_at=data["created_at"],
            name=data["name"],
            shortcut_icon_base_url=data["shortcut_icon_base_url"],
            strava_redirect_uri=data["strava_redirect_uri"],
            open_weather_api_key=env.OPEN_WEATHER_MAP_API_KEY,
            location_iq_api_key=env.LOCATION_IQ_API_KEY,
            unsplash_api_key=env.UNSPLASH_API_KEY,
            strava_client_id=env.STRAVA_CLIENT_ID,
            strava_client_secret=env.STRAVA_CLIENT_SECRET,
        )

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving Start Settings for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while retrieving the Start Settings" + str(e)
        )
