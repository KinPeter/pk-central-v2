import json
import requests
from pathlib import Path

from local.seeder import Seeder


def seed():
    seeder = Seeder()
    base_url, headers = seeder.get_api_credentials()

    file_path = Path(__file__).resolve().parents[2] / ".temp" / "v1_backup.json"

    with open(file_path, "r") as f:
        backup = json.load(f)

    data = backup["startSettings"]
    body = {
        "name": data["name"],
        "shortcutIconBaseUrl": data["shortcutIconBaseUrl"],
        "stravaRedirectUri": data["stravaRedirectUri"],
    }
    response = requests.put(f"{base_url}/start-settings/", headers=headers, json=body)
    if response.status_code == 200:
        print(f"Item seeded successfully.")
    else:
        print(f"Failed to seed item: {response.text}")
        exit(1)

    print("Seeding completed.")


if __name__ == "__main__":
    seed()
