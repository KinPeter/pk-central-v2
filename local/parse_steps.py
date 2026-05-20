#!/usr/bin/env python3
import csv
import json
from datetime import datetime
from pathlib import Path


def load_steps(path):
    with open(path, encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return [
            {"day_time": int(row["day_time"]), "step_count": int(row["step_count"])}
            for row in reader
            if row.get("day_time") and row.get("step_count")
        ]


"""
Parses the steps from the CSV file exported from Samsung Health app and writes the entry with the highest steps count per day to a JSON file.

File to parse from the exports:
    com.samsung.shealth.tracker.pedometer_day_summary.<timestamp>.csv

Usage:
    Run from the project root:
    python ./local/parse_steps.py

Output format:
[
  {
    "2021.04.14": 2756
  },
  {
    "2021.04.15": 5641
  },
  ...
]
"""
if __name__ == "__main__":
    csv_path = Path(".temp/sh-steps-backup.csv")
    rows = load_steps(csv_path)

    best_per_day = {}
    for row in rows:
        date = datetime.fromtimestamp(row["day_time"] / 1000).strftime("%Y.%m.%d")
        steps = row["step_count"]
        if date not in best_per_day or steps > best_per_day[date]:
            best_per_day[date] = steps

    result = [{date: steps} for date, steps in sorted(best_per_day.items())]

    out_path = csv_path.with_suffix(".json")
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")
