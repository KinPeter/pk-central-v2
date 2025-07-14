import json
from pathlib import Path

from local.seeder import Seeder


def seed_static_data():
    seeder = Seeder()
    db = seeder.get_db()

    aircrafts_file = (
        Path(__file__).resolve().parents[2] / "app" / "static_data" / "aircrafts.json"
    )
    airlines_file = (
        Path(__file__).resolve().parents[2] / "app" / "static_data" / "airlines.json"
    )

    with open(aircrafts_file, "r") as f:
        aircrafts_data = json.load(f)
        db.get_collection("aircrafts").insert_many(aircrafts_data)
    print("Aircrafts data seeded.")

    with open(airlines_file, "r") as f:
        airlines_data = json.load(f)
        db.get_collection("airlines").insert_many(airlines_data)
    print("Airlines data seeded.")

    seeder.close_db()


if __name__ == "__main__":
    seed_static_data()
