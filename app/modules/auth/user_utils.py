from datetime import datetime, timezone
from logging import Logger
import uuid
from app.common.db import DbCollection
from app.common.email import EmailManager
from app.common.environment import PkCentralEnv
from app.common.types import AsyncDatabase
from app.modules.activities.activities_utils import create_initial_activities_config
from app.modules.auth.auth_utils import get_login_code
from app.modules.reddit.reddit_utils import create_initial_reddit_config
from app.modules.start_settings.start_settings_utils import create_initial_settings


async def sign_up_or_login_user(
    email: str,
    send_emails: bool,
    env: PkCentralEnv,
    db: AsyncDatabase,
    email_manager: EmailManager | None,
    logger: Logger,
) -> str:
    """
    Sign up or log in a user by their email address.
    If the user does not exist, create a new user.
    """
    users_collection = db.get_collection(DbCollection.USERS)
    existing_user = await users_collection.find_one({"email": email})

    user = None

    if existing_user:
        user = existing_user
    else:
        user = await create_initial_user(email, db, logger)
        if send_emails and env.PK_ENV.lower() != "test" and email_manager is not None:
            email_manager.send_signup_notification(email)

    login_code_data = get_login_code(env.LOGIN_CODE_EXPIRY)

    await users_collection.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "login_code_hash": login_code_data.hashed_login_code,
                "login_code_salt": login_code_data.salt,
                "login_code_expires": login_code_data.expiry,
            }
        },
    )

    if send_emails and env.PK_ENV.lower() != "test" and email_manager is not None:
        email_manager.send_login_code(email, login_code_data.login_code)

    return login_code_data.login_code


async def create_initial_user(email: str, db: AsyncDatabase, logger: Logger) -> dict:
    """
    Create an initial user with the given email address.
    Returns the user object.
    """
    users_collection = db.get_collection(DbCollection.USERS)

    user = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc),
        "email": email,
        "login_code_hash": None,
        "login_code_salt": None,
        "login_code_expires": None,
        "password_hash": None,
        "password_salt": None,
    }
    await users_collection.insert_one(user)

    logger.info(f"New user created with email: {email} (ID: {user['id']})")
    await create_initial_settings(db, logger, user["id"])
    await create_initial_activities_config(db, logger, user["id"])
    await create_initial_reddit_config(db, logger, user["id"])

    return user
