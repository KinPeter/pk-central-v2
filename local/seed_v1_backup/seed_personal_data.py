import json
from time import sleep
import requests
from pathlib import Path

from local.seeder import Seeder


def seed():
    seeder = Seeder()
    base_url, headers = seeder.get_api_credentials()

    file_path = Path(__file__).resolve().parents[2] / ".temp" / "v1_backup.json"

    with open(file_path, "r") as f:
        backup = json.load(f)

    data = backup["personalData"]
    success = 0
    failure = 0

    for item in data:
        body = {
            "name": item["name"],
            "identifier": item["identifier"],
            "expiry": item.get("expiry", None),
        }
        response = requests.post(
            f"{base_url}/personal-data/", headers=headers, json=body
        )
        if response.status_code == 201:
            success += 1
            print(f"Item {item['name']} seeded successfully.")
        else:
            failure += 1
            print(f"Failed to seed item {item['name']}: {response.text}")

        sleep(0.2)  # To avoid hitting the API too fast

    print(f"Seeding completed: {success} items successful, {failure} items failed.")


if __name__ == "__main__":
    seed()
