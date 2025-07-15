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

    data = backup["visits"]
    success = 0
    failure = 0

    for item in data:
        body = {
            "city": item["city"],
            "country": item["country"],
            "lat": item["lat"],
            "lng": item["lng"],
            "year": item.get("year", None) or None,
        }
        response = requests.post(f"{base_url}/visits/", headers=headers, json=body)
        if response.status_code == 201:
            success += 1
            print(f"Item {item['city']} seeded successfully.")
        else:
            failure += 1
            print(f"Failed to seed item {item['city']}: {response.text}")

        sleep(seeder.sleep_time)  # To avoid hitting the API too fast

    print(f"Seeding completed: {success} items successful, {failure} items failed.")


if __name__ == "__main__":
    seed()
