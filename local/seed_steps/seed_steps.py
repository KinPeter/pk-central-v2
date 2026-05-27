import json
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()


def seed():
    user_id = os.getenv("SEED_USER_ID")
    if not user_id:
        raise ValueError("SEED_USER_ID environment variable is not set.")

    host = os.getenv("MONGODB_URI")
    if not host:
        raise ValueError("MONGODB_URI environment variable is not set.")

    db_name = os.getenv("MONGODB_NAME")
    if not db_name:
        raise ValueError("MONGODB_NAME environment variable is not set.")

    client = MongoClient(
        host=host,
        connectTimeoutMS=5000,
        server_api=ServerApi("1"),
    )
    db = client.get_database(db_name)
    collection = db.get_collection("steps")

    file_path = Path(__file__).resolve().parents[2] / ".temp" / "sh-steps-backup.json"
    with open(file_path) as f:
        raw_entries = json.load(f)

    docs = []
    for entry in raw_entries:
        for date_str, steps in entry.items():
            date = date_str.replace(".", "-")
            docs.append(
                {
                    "date": date,
                    "steps": steps,
                    "user_id": user_id,
                }
            )

    if docs:
        collection.insert_many(docs, ordered=False)

    print(f"Seeded {len(docs)} step entries.")
    client.close()


if __name__ == "__main__":
    seed()
