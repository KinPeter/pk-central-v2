from fastapi import HTTPException
import httpx

from .logger import get_logger


class StravaApi:
    """
    A class to handle Strava API interactions.
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://www.strava.com/api/v3"
        self.logger = get_logger()

    async def get_athlete(self):
        """
        Fetch the authenticated athlete's profile.
        """
        return await self._get_request("/athlete")

    async def get_activities(
        self,
        page: int = 1,
        per_page: int = 50,
        after: int | None = None,
        before: int | None = None,
    ):
        """
        Fetch a list of activities for the authenticated athlete.
        """
        params = {"page": page, "per_page": per_page}
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        return await self._get_request("/athlete/activities", params=params)

    async def get_all_activities(
        self,
        per_page: int = 50,
        after: int | None = None,
        before: int | None = None,
    ):
        """
        Fetch all activities for the authenticated athlete, handling pagination.
        """
        all_activities = []
        page = 1
        while True:
            activities = await self.get_activities(
                page=page,
                per_page=per_page,
                after=after,
                before=before,
            )
            if not activities:
                break
            all_activities.extend(activities)
            page += 1
        return all_activities

    async def get_activity_latlng_stream(self, activity_id: int):
        """
        Fetch the location (latlng) activity streams for a specific activity.
        """
        params = {"keys": "latlng", "key_by_type": "true"}
        return await self._get_request(
            f"/activities/{activity_id}/streams", params=params
        )

    async def _get_request(self, endpoint: str, params: dict | None = None):
        """
        Generic GET request to the Strava API.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.logger.info(
            f"Making GET request to Strava API: {endpoint} with params: {params}"
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            try:
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                self.logger.error(
                    f"Error during Strava API call {url}: {exc.response.status_code} - {exc.response.text}"
                )
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=f"Strava API error: {exc.response.text}",
                )
