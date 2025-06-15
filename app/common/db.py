from enum import Enum
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

from app.common.environment import PkCentralEnv
from app.common.types import AsyncDatabase
from app.common.logger import get_logger


class DbCollection(str, Enum):
    USERS = "users"
    ACTIVITIES = "activities"
    SYNC_METADATA = "sync_metadata"


class MongoDbManager:
    """
    This class handles the connection to MongoDB, provides access to the database,
    and ensures proper cleanup of resources.
    """

    def __init__(self, env: PkCentralEnv):
        self.logger = get_logger()
        self.env = env
        self.mongo_client = None
        self.db = None

    async def connect(self) -> AsyncDatabase:
        await self._initiate()

        if self.db is None:
            raise ValueError("No MongoDB instance after initiation.")

        return self.db

    async def close(self):
        if self.mongo_client:
            await self.mongo_client.close()
            self.logger.info("MongoDB connection closed.")

    async def _initiate(self):
        self.logger.info("Connecting to MongoDB...")
        mongodb_uri = self.env.MONGODB_URI
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable is not set.")

        mongodb_name = self.env.MONGODB_NAME
        if not mongodb_name:
            raise ValueError("MONGODB_NAME environment variable is not set.")

        try:
            self.mongo_client = AsyncMongoClient(
                host=mongodb_uri, connectTimeoutMS=5000, server_api=ServerApi("1")
            )
            self.db = self.mongo_client.get_database(mongodb_name)
            await self.mongo_client.admin.command("ping")
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise

        self.logger.info(f"Connected to MongoDB database: {mongodb_name}")
