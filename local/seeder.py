import os
import dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi


class Seeder:
    def __init__(self):
        dotenv.load_dotenv()

    def get_api_credentials(self):
        seed_token = os.getenv("SEED_TOKEN")
        if not seed_token:
            raise ValueError("SEED_TOKEN environment variable is not set.")

        base_url = os.getenv("SEED_URL")
        if not base_url:
            raise ValueError("SEED_URL environment variable is not set.")

        headers = {"Authorization": f"Bearer {seed_token}"}
        return base_url, headers

    def get_db(self):
        db_url = os.getenv("MONGODB_URI")
        if not db_url:
            raise ValueError("MONGODB_URI environment variable is not set.")
        db_name = os.getenv("MONGODB_NAME")
        if not db_name:
            raise ValueError("MONGODB_NAME environment variable is not set.")
        try:
            self.client = MongoClient(
                host=db_url, connectTimeoutMS=5000, server_api=ServerApi("1")
            )
            db = self.client.get_database(db_name)
            self.client.admin.command("ping")
            print(f"Connected to MongoDB database: {db_name}")
            return db

        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

    def close_db(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")
