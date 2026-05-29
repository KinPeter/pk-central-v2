from logging import Logger
import httpx
from fastapi import HTTPException
from typing import List

from app.common.environment import PkCentralEnv
from app.modules.activities.activities_types import StepsItem


class StepsSyncApi:
    def __init__(self, env: PkCentralEnv, logger: Logger):
        self.url = env.STEPS_SYNC_URL
        self.api_key = env.STEPS_SYNC_API_KEY
        self.logger = logger

    async def fetch_steps(
        self, from_date: str | None = None, to_date: str | None = None
    ) -> List[StepsItem]:
        params = {"apiKey": self.api_key}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            try:
                response = await client.get(self.url, params=params)
                response.raise_for_status()
                json = response.json()
                return [
                    StepsItem(steps=item["steps"], date=item["date"]) for item in json
                ]
            except httpx.HTTPStatusError as exc:
                self.logger.error(
                    f"Error during StepsSync API call {self.url}: {exc.response.status_code} - {exc.response.text}"
                )
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=f"StepsSync API error: {exc.response.text}",
                )
            except httpx.RequestError as exc:
                self.logger.error(
                    f"Request failed for StepsSync API {self.url}: {repr(exc)}"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"StepsSync API request failed: {repr(exc)}",
                )
            except Exception as exc:
                self.logger.error(
                    f"Unexpected error during StepsSync API call: {repr(exc)}"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected error during StepsSync API call: {repr(exc)}",
                )
