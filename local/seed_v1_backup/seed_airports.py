import json
from pathlib import Path

from local.seeder import Seeder


def seed():
    seeder = Seeder()
    db = seeder.get_db()

    file_path = Path(__file__).resolve().parents[2] / ".temp" / "v1_backup.json"

    with open(file_path, "r") as f:
        backup = json.load(f)

    data = backup["flights"]
    airports = []

    for item in data:
        if not any(item["from"]["iata"] == airport["iata"] for airport in airports):
            airports.append(
                {
                    "iata": item["from"]["iata"],
                    "icao": item["from"]["icao"],
                    "name": item["from"]["name"],
                    "city": item["from"]["city"],
                    "country": item["from"]["country"],
                    "lat": item["from"]["lat"],
                    "lng": item["from"]["lng"],
                }
            )

        if not any(item["to"]["iata"] == airport["iata"] for airport in airports):
            airports.append(
                {
                    "iata": item["to"]["iata"],
                    "icao": item["to"]["icao"],
                    "name": item["to"]["name"],
                    "city": item["to"]["city"],
                    "country": item["to"]["country"],
                    "lat": item["to"]["lat"],
                    "lng": item["to"]["lng"],
                }
            )

    db.get_collection("airports").insert_many(airports)

    seeder.close_db()


if __name__ == "__main__":
    seed()
