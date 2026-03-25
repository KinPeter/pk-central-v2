import uuid
from datetime import datetime, timezone
from logging import Logger
from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException
from app.common.types import AsyncDatabase
from app.modules.auth.auth_types import CurrentUser, GenerateApiKeyRequest, GenerateApiKeyResponse
from app.modules.auth.auth_utils import generate_api_key_data


async def generate_api_key(body: GenerateApiKeyRequest, request: Request, user: CurrentUser) -> GenerateApiKeyResponse:
    """
    Generate a new API key for the authenticated user.
    The raw key is returned once and never stored — only its SHA-256 hash is persisted.
    """
    logger: Logger = request.app.state.logger
    db: AsyncDatabase = request.app.state.db

    try:
        raw_key, hashed_key = generate_api_key_data()
        key_id = str(uuid.uuid4())

        api_key_doc = {
            "id": key_id,
            "user_id": user.id,
            "name": body.name,
            "hashed_key": hashed_key,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used_at": None,
        }

        await db.get_collection(DbCollection.API_KEYS).insert_one(api_key_doc)

        logger.info(f"API key generated for user {user.id} (key id: {key_id})")

        return GenerateApiKeyResponse(id=key_id, api_key=raw_key)

    except Exception as e:
        logger.error(f"Error generating API key for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while generating the API key. Please try again later."
        )
