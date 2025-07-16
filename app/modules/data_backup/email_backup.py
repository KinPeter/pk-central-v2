import json
from logging import Logger
from fastapi import Request

from app.common.db import DbCollection
from app.common.email import EmailAttachment, EmailManager
from app.common.environment import PkCentralEnv
from app.common.responses import InternalServerErrorException, MessageResponse
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import CurrentUser


def remove_ids(docs):
    for doc in docs:
        if "_id" in doc:
            doc.pop("_id")
    return docs


async def email_backup(request: Request, user: CurrentUser) -> MessageResponse:
    db: AsyncDatabase = request.app.state.db
    env: PkCentralEnv = request.app.state.env
    logger: Logger = request.app.state.logger

    email_manager = EmailManager(env)

    try:
        user_data = await db.get_collection(DbCollection.USERS).find_one(
            {"id": user.id}
        )
        start_settings = await db.get_collection(DbCollection.START_SETTINGS).find_one(
            {"user_id": user.id}
        )
        activities = await db.get_collection(DbCollection.ACTIVITIES).find_one(
            {"user_id": user.id}
        )
        reddit = await db.get_collection(DbCollection.REDDIT).find_one(
            {"user_id": user.id}
        )
        flights = (
            await db.get_collection(DbCollection.FLIGHTS)
            .find({"user_id": user.id})
            .to_list(length=None)
        )
        visits = (
            await db.get_collection(DbCollection.VISITS)
            .find({"user_id": user.id})
            .to_list(length=None)
        )
        notes = (
            await db.get_collection(DbCollection.NOTES)
            .find({"user_id": user.id})
            .to_list(length=None)
        )
        personal_data = (
            await db.get_collection(DbCollection.PERSONAL_DATA)
            .find({"user_id": user.id})
            .to_list(length=None)
        )
        shortcuts = (
            await db.get_collection(DbCollection.SHORTCUTS)
            .find({"user_id": user.id})
            .to_list(length=None)
        )
        birthdays = (
            await db.get_collection(DbCollection.BIRTHDAYS)
            .find({"user_id": user.id})
            .to_list(length=None)
        )
        aircrafts = (
            await db.get_collection(DbCollection.AIRCRAFTS).find().to_list(length=None)
        )
        airlines = (
            await db.get_collection(DbCollection.AIRLINES).find().to_list(length=None)
        )
        airports = (
            await db.get_collection(DbCollection.AIRPORTS).find().to_list(length=None)
        )

        email = user_data.get("email") if user_data else None
        name = start_settings.get("name") if start_settings else "User"

        if not email:
            logger.error("User email not found, cannot send backup email.")
            raise ValueError("User email not found")

        user_data.pop("_id", None) if user_data else {}
        start_settings.pop("_id", None) if start_settings else {}
        activities.pop("_id", None) if activities else {}
        reddit.pop("_id", None) if reddit else {}
        flights = remove_ids(flights)
        visits = remove_ids(visits)
        notes = remove_ids(notes)
        personal_data = remove_ids(personal_data)
        shortcuts = remove_ids(shortcuts)
        birthdays = remove_ids(birthdays)
        aircrafts = remove_ids(aircrafts)
        airlines = remove_ids(airlines)
        airports = remove_ids(airports)

        files = [
            EmailAttachment(
                content=json.dumps(user_data, default=str, ensure_ascii=False),
                filename=f"user_data.json",
            ),
            EmailAttachment(
                content=json.dumps(start_settings, default=str, ensure_ascii=False),
                filename=f"start_settings.json",
            ),
            EmailAttachment(
                content=json.dumps(activities, default=str, ensure_ascii=False),
                filename=f"activities.json",
            ),
            EmailAttachment(
                content=json.dumps(flights, default=str, ensure_ascii=False),
                filename=f"flights.json",
            ),
            EmailAttachment(
                content=json.dumps(visits, default=str, ensure_ascii=False),
                filename=f"visits.json",
            ),
            EmailAttachment(
                content=json.dumps(notes, default=str, ensure_ascii=False),
                filename=f"notes.json",
            ),
            EmailAttachment(
                content=json.dumps(personal_data, default=str, ensure_ascii=False),
                filename=f"personal_data.json",
            ),
            EmailAttachment(
                content=json.dumps(reddit, default=str, ensure_ascii=False),
                filename=f"reddit.json",
            ),
            EmailAttachment(
                content=json.dumps(shortcuts, default=str, ensure_ascii=False),
                filename=f"shortcuts.json",
            ),
            EmailAttachment(
                content=json.dumps(birthdays, default=str, ensure_ascii=False),
                filename=f"birthdays.json",
            ),
            EmailAttachment(
                content=json.dumps(aircrafts, default=str, ensure_ascii=False),
                filename=f"aircrafts.json",
            ),
            EmailAttachment(
                content=json.dumps(airlines, default=str, ensure_ascii=False),
                filename=f"airlines.json",
            ),
            EmailAttachment(
                content=json.dumps(airports, default=str, ensure_ascii=False),
                filename=f"airports.json",
            ),
        ]

        email_manager.send_data_backup(
            name=name,
            email=email,
            files=files,
        )

        return MessageResponse(message="Data backup email sent successfully.")

    except Exception as e:
        logger.error(f"Error fetching user data: {e}")
        raise InternalServerErrorException("Failed to fetch user data")
