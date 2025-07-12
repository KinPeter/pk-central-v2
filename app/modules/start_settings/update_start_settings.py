from fastapi import Request
from app.common.db import DbCollection
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.auth.auth_types import CurrentUser
from app.modules.start_settings.start_settings_types import (
    StartSettings,
    StartSettingsRequest,
)


async def update_start_settings(
    request: Request,
    body: StartSettingsRequest,
    user: CurrentUser,
) -> StartSettings:
    """
    Update the Start Settings for the current user.
    """
    db = request.app.state.db
    logger = request.app.state.logger
    env: PkCentralEnv = request.app.state.env

    try:
        collection = db.get_collection(DbCollection.START_SETTINGS)
        result = await collection.update_one(
            {"user_id": user.id},
            {
                "$set": body.model_dump(
                    exclude_none=True, exclude_unset=True, mode="json"
                )
            },
        )

        if result.matched_count == 0:
            logger.error(f"Failed to update Start Settings for user {user.id}")
            raise NotFoundException(resource="Start Settings")

        updated_data = await collection.find_one({"user_id": user.id})

        return StartSettings(
            id=updated_data["id"],
            created_at=updated_data["created_at"],
            name=updated_data["name"],
            shortcut_icon_base_url=updated_data["shortcut_icon_base_url"],
            strava_redirect_uri=updated_data["strava_redirect_uri"],
            open_weather_api_key=env.OPEN_WEATHER_MAP_API_KEY,
            location_iq_api_key=env.LOCATION_IQ_API_KEY,
            unsplash_api_key=env.UNSPLASH_API_KEY,
            strava_client_id=env.STRAVA_CLIENT_ID,
            strava_client_secret=env.STRAVA_CLIENT_SECRET,
        )

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating Start Settings for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while updating the Start Settings" + str(e)
        )
