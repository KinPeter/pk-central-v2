import uuid
from datetime import datetime, timezone
from fastapi import Request
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException
from app.modules.auth.auth_types import CurrentUser
from app.modules.strava.strava_api import StravaApi
from app.modules.strava.strava_types import StravaDbCollection, StravaSyncResponse


async def sync_strava_routes(
    request: Request, user: CurrentUser, strava_token: str, force: bool | None = False
):
    """
    Endpoint to sync Strava data for the current user.
    If `force` is True, it will force a sync even if the last sync was recent.
    """
    env: PkCentralEnv = request.app.state.env
    logger = request.app.state.logger
    db_client = AsyncMongoClient(
        host=env.STRAVA_DB_URI, connectTimeoutMS=5000, server_api=ServerApi("1")
    )
    try:
        await db_client.admin.command("ping")
    except Exception as e:
        logger.error(f"Error connecting to Strava database: {e}")
        raise InternalServerErrorException(
            detail="Failed to connect to Strava database. " + str(e)
        )

    just_synced_count = 0
    try:
        db = db_client.get_database("strava")
        strava = StravaApi(access_token=strava_token, logger=logger)
        activities_collection = db.get_collection(StravaDbCollection.ACTIVITIES)
        sync_meta_collection = db.get_collection(StravaDbCollection.SYNC_META)

        user_sync_data = await sync_meta_collection.find_one({"user_id": user.id})
        if not user_sync_data:
            logger.info(
                f"No sync metadata found for user {user.id}, creating new entry."
            )
            user_sync_data = {"user_id": user.id, "synced_ids": [], "last_synced": None}
            await sync_meta_collection.insert_one(user_sync_data)

        logger.info(f"Syncing routes for user {user.id}")

        athlete = await strava.get_athlete()
        logger.info(
            f"Authenticated as athlete: {athlete['username']} ({athlete['id']})"
        )

        if force is True:
            logger.info("Force is True, fetching all activities.")
            activities = await strava.get_all_activities()
        elif user_sync_data["last_synced"] is not None:
            logger.info(
                f"Last synced time found: {user_sync_data['last_synced']}, fetching activities since then."
            )
            dt = datetime.fromisoformat(
                user_sync_data["last_synced"].replace("Z", "+00:00")
            )
            epoch_ts = int(dt.timestamp())
            activities = await strava.get_all_activities(after=epoch_ts)
        else:
            logger.info("No last synced time found, fetching all activities.")
            activities = await strava.get_all_activities()

        logger.info(f"Fetched {len(activities)} activities for athlete {athlete['id']}")

        if not activities:
            logger.info("No activities found to sync.")
            saved_count = await activities_collection.count_documents(
                {"user_id": user.id}
            )
            return StravaSyncResponse(
                routes_synced=0,
                total_routes=saved_count,
            )

        already_synced = set(user_sync_data["synced_ids"])

        for activity in activities:
            strava_id = activity["id"]

            if strava_id in already_synced:
                logger.info(f"Activity {strava_id} already synced, skipping.")
                continue

            if activity["type"] not in ["Walk", "Run", "Ride"]:
                logger.info(
                    f"Activity {strava_id} is of type {activity['type']}, skipping."
                )
                continue

            stream_response = await strava.get_activity_latlng_stream(
                activity_id=strava_id
            )

            if (
                not stream_response
                or "latlng" not in stream_response
                or not stream_response["latlng"]["data"]
            ):
                logger.info(
                    f"No lat/lng stream found for activity {strava_id}, skipping."
                )
                continue

            latlng_data = stream_response["latlng"]["data"]
            logger.info(
                f"Activity {strava_id} has lat/lng data with length: {len(latlng_data)}, syncing..."
            )

            activity_with_route = {
                "id": str(uuid.uuid4()),
                "strava_id": strava_id,
                "user_id": user.id,
                "name": activity.get("name", "Unnamed Activity"),
                "start_date": datetime.fromisoformat(
                    activity["start_date"].replace("Z", "+00:00")
                ),
                "distance": activity["distance"],
                "type": activity["type"],
                "route": latlng_data,
            }
            await activities_collection.insert_one(activity_with_route)

            user_sync_data["synced_ids"].append(strava_id)
            user_sync_data["last_synced"] = datetime.now(timezone.utc).isoformat()
            await sync_meta_collection.update_one(
                {"user_id": user.id},
                {"$set": user_sync_data},
            )
            just_synced_count += 1
            logger.info(f"Synced activity {strava_id} for user {user.id}")

        logger.info(
            f"Successfully synced {just_synced_count} activities for user {user.id}"
            if just_synced_count > 0
            else "No new activities were synced."
        )
        return StravaSyncResponse(
            routes_synced=just_synced_count,
            total_routes=len(user_sync_data["synced_ids"]),
        )

    except Exception as e:
        logger.info(
            f"Synced {just_synced_count} activities for {user.id} before the error."
        )
        logger.error(f"Error syncing routes for user {user.id}: {str(e)}")
        raise InternalServerErrorException(
            detail=f"Could not finish syncing routes from Strava. (Synced {just_synced_count} before the error.) - {str(e)}",
        )

    finally:
        await db_client.close()
        logger.info("Strava sync completed, MongoDB connection closed.")
