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

    for item in data:
        response = requests.post(f"{base_url}/birthdays", headers=headers, json=item)
        if response.status_code == 201:
            print(f"Item {item['name']} seeded successfully.")
        else:
            print(f"Failed to seed item {item['name']}: {response.text}")

        sleep(0.2)  # To avoid hitting the API too fast

    print("Seeding completed.")


if __name__ == "__main__":
    seed()
