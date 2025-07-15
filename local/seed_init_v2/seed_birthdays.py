import json
from time import sleep
import requests
from pathlib import Path

from local.seeder import Seeder


def seed():
    seeder = Seeder()
    base_url, headers = seeder.get_api_credentials()

    file_path = Path(__file__).resolve().parents[2] / ".temp" / "bdays.json"

    with open(file_path, "r") as f:
        data = json.load(f)

    success = 0
    failure = 0

    for item in data:
        response = requests.post(f"{base_url}/birthdays/", headers=headers, json=item)
        if response.status_code == 201:
            success += 1
            print(f"Item {item['name']} seeded successfully.")
        else:
            failure += 1
            print(f"Failed to seed item {item['name']}: {response.text}")

        sleep(seeder.sleep_time)  # To avoid hitting the API too fast

    print(f"Seeding completed: {success} items successful, {failure} items failed.")


if __name__ == "__main__":
    seed()
