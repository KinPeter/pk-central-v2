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

    data = backup["activities"]
    body = {
        "cyclingMonthlyGoal": data["cyclingMonthlyGoal"],
        "cyclingWeeklyGoal": data["cyclingWeeklyGoal"],
        "walkMonthlyGoal": data["walkMonthlyGoal"],
        "walkWeeklyGoal": data["walkWeeklyGoal"],
    }

    response = requests.patch(
        f"{base_url}/activities/goals", headers=headers, json=body
    )
    if response.status_code == 200:
        print(f"Item seeded successfully.")
    else:
        print(f"Failed to seed item: {response.text}")
        exit(1)

    chore = data["chores"][0]
    body = {
        "name": chore["name"],
        "lastKm": chore["lastKm"],
        "kmInterval": chore["kmInterval"],
    }
    response = requests.post(
        f"{base_url}/activities/chores", headers=headers, json=body
    )
    if response.status_code == 201:
        print(f"Item seeded successfully.")
    else:
        print(f"Failed to seed item: {response.text}")
        exit(1)

    print("Seeding completed.")


if __name__ == "__main__":
    seed()
