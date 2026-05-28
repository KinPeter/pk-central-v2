from logging import Logger
from fastapi import Request

from app.common.date_utils import add_one_day
from app.common.db import DbCollection
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException
from app.common.types import AsyncDatabase
from app.modules.activities.activities_types import StepsSyncResponse
from app.modules.activities.steps_sync_api import StepsSyncApi
from app.modules.auth.auth_types import CurrentUser


async def sync_steps(request: Request, user: CurrentUser) -> StepsSyncResponse:
    """
    Endpoint to sync steps data from Samsung Health via a Google Apps Script API
    """
    env: PkCentralEnv = request.app.state.env
    logger: Logger = request.app.state.logger
    db: AsyncDatabase = request.app.state.db

    just_synced_count = 0
    total_days = 0

    try:
        sync_api = StepsSyncApi(env, logger)
        steps_collection = db.get_collection(DbCollection.STEPS)
        sync_meta_collection = db.get_collection(DbCollection.STEPS_SYNC_META)

        total_days = await steps_collection.count_documents({"user_id": user.id})

        user_sync_data = await sync_meta_collection.find_one({"user_id": user.id})
        if not user_sync_data:
            logger.info(
                f"No steps sync metadata found for user {user.id}, creating new entry."
            )
            user_sync_data = {"user_id": user.id, "last_synced_day": None}
            await sync_meta_collection.insert_one(user_sync_data)

        logger.info(f"Syncing steps for user {user.id}")

        if user_sync_data.get("last_synced_day"):
            logger.info(
                f"User {user.id} has already synced steps up to {user_sync_data['last_synced_day']}"
            )
            from_date = add_one_day(user_sync_data["last_synced_day"])
            steps_to_sync = await sync_api.fetch_steps(from_date=from_date)
        else:
            logger.info(f"User {user.id} has never synced steps before")
            steps_to_sync = await sync_api.fetch_steps()

        length_to_sync = len(steps_to_sync)

        if length_to_sync == 0:
            logger.info(f"No new steps to sync for user {user.id}")
            return StepsSyncResponse(days_synced=0, total_days=total_days)

        logger.info(f"Found {length_to_sync} days of steps to sync for user {user.id}")

        # loop through the steps to sync and check if it is already in the DB. If not, insert it.

        for steps_item in steps_to_sync:
            if await steps_collection.find_one(
                {"user_id": user.id, "date": steps_item.date}
            ):
                logger.info(
                    f"Steps for {steps_item.date} already exist for user {user.id}"
                )
                continue

            doc = {
                "user_id": user.id,
                "steps": steps_item.steps,
                "date": steps_item.date,
            }
            await steps_collection.insert_one(doc)
            just_synced_count += 1
            total_days += 1

            # update the last synced day
            await sync_meta_collection.update_one(
                {"user_id": user.id},
                {"$set": {"last_synced_day": steps_item.date}},
            )

            logger.info(f"Synced steps for {steps_item.date} for user {user.id}")

        return StepsSyncResponse(days_synced=just_synced_count, total_days=total_days)

    except Exception as e:
        logger.info(f"Synced {just_synced_count} days for {user.id} before the error.")
        logger.error(f"Error syncing steps for user {user.id}: {str(e)}")
        raise InternalServerErrorException(
            detail=f"Could not finish syncing steps. (Synced {just_synced_count} before the error.) - {str(e)}",
        )
