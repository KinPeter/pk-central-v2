from app.common.responses import OkResponse
from app.common.types import BaseEntity, PkBaseModel
from pydantic import HttpUrl


class StartSettings(OkResponse, BaseEntity):
    name: str | None = None
    shortcut_icon_base_url: str | None = None
    birthdays_url: str | None = None
    strava_redirect_uri: str | None = None
    # coming from environment variables:
    open_weather_api_key: str | None = None
    location_iq_api_key: str | None = None
    unsplash_api_key: str | None = None
    strava_client_id: str | None = None
    strava_client_secret: str | None = None


class StartSettingsRequest(PkBaseModel):
    name: str | None = None
    shortcut_icon_base_url: HttpUrl | None = None
    birthdays_url: HttpUrl | None = None
    strava_redirect_uri: HttpUrl | None = None
