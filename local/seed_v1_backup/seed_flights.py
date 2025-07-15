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

    data = backup["flights"]
    success = 0
    failure = 0

    for item in data:
        body = {
            "date": item["date"],
            "flightNumber": item["flightNumber"],
            "departureAirport": item["from"],
            "arrivalAirport": item["to"],
            "departureTime": ":".join(item["departureTime"].split(":")[0:2]),
            "arrivalTime": ":".join(item["arrivalTime"].split(":")[0:2]),
            "duration": ":".join(item["duration"].split(":")[0:2]),
            "airline": item["airline"],
            "aircraft": item["aircraft"],
            "registration": item["registration"] or None,
            "seatNumber": item["seatNumber"] or None,
            "seatType": item["seatType"],
            "flightClass": item["flightClass"],
            "flightReason": item["flightReason"],
            "distance": item["distance"],
            "note": item["note"] or None,
            "isPlanned": item.get("isPlanned", False),
        }
        response = requests.post(f"{base_url}/flights/", headers=headers, json=body)
        if response.status_code == 201:
            success += 1
            print(f"Item {item['flightNumber']}/{item['date']} seeded successfully.")
        else:
            failure += 1
            print(
                f"Failed to seed item {item['flightNumber']}/{item['date']}: {response.text}"
            )

        sleep(seeder.sleep_time)  # To avoid hitting the API too fast

    print(f"Seeding completed: {success} items successful, {failure} items failed.")


if __name__ == "__main__":
    seed()
