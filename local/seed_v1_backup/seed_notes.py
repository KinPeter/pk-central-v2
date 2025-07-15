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

    data = backup["notes"]
    success = 0
    failure = 0

    for item in data:
        body = {
            "text": item["text"] or None,
            "links": item["links"] or [],
            "archived": item.get("archived", False),
            "pinned": item.get("pinned", False),
        }
        response = requests.post(f"{base_url}/notes/", headers=headers, json=body)
        if response.status_code == 201:
            success += 1
            print(
                f"Item {item['createdAt']}/{item.get('text','')} seeded successfully."
            )
        else:
            failure += 1
            print(
                f"Failed to seed item {item['createdAt']}/{item.get('text', '')}: {response.text}"
            )

        sleep(0.2)  # To avoid hitting the API too fast

    print(f"Seeding completed: {success} items successful, {failure} items failed.")


if __name__ == "__main__":
    seed()
