import json
from time import sleep
import requests
from pathlib import Path

from local.seeder import Seeder


def seed():
    seeder = Seeder()
    base_url, headers = seeder.get_api_credentials()

    file_path = Path(__file__).resolve().parents[2] / ".temp" / "reddit.json"

    with open(file_path, "r") as f:
        data = json.load(f)

    body = {
        "sets": data["sets"],
        "blockedUsers": data["blocked_users"],
    }

    response = requests.put(f"{base_url}/reddit/config", headers=headers, json=body)
    if response.status_code == 200:
        print(f"Item seeded successfully.")
    else:
        print(f"Failed to seed item: {response.text}")
        exit(1)

    print("Seeding completed.")


if __name__ == "__main__":
    seed()
