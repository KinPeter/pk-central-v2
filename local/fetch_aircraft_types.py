import requests
import json


def fetch_aircraft_types():
    """Fetch aircraft types from ICAO and save to file"""
    url = "https://www4.icao.int/doc8643/External/AircraftTypes"

    try:
        print("Sending POST request to ICAO...")
        response = requests.post(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        print(f"Response status: {response.status_code}")
        print(f"Content length: {len(response.text)} characters")

        # Save raw response
        with open("aircraft_types_raw.json", "w", encoding="utf-8") as f:
            f.write(response.text)

        # Try to parse and save formatted JSON
        try:
            data = response.json()
            with open("aircraft_types.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(
                f"✓ Saved formatted JSON with {len(data) if isinstance(data, list) else 'unknown'} records"
            )
        except json.JSONDecodeError:
            print("⚠ Response is not valid JSON, saved raw text only")

        print("✓ Files saved successfully!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False


def filter_and_map_landplane_aircraft(
    input_file="aircraft_types.json", output_file="landplane_aircraft.json"
):
    """
    Filter aircraft to only LandPlane types and map to simplified structure.

    Output format:
    {
        "icao": "ICAO designator code",
        "name": "ManufacturerCode ModelFullName"
    }
    """

    # Load the data
    with open(input_file, "r", encoding="utf-8") as f:
        all_aircraft = json.load(f)

    # Filter for LandPlane aircraft and map to new structure
    landplane_aircraft = []

    for aircraft in all_aircraft:
        if aircraft.get("AircraftDescription") == "LandPlane":
            # Format manufacturer name based on length
            manufacturer = aircraft.get("ManufacturerCode", "")
            if len(manufacturer) > 4:
                # Capitalize each word for longer manufacturer names
                manufacturer = manufacturer.title()

            # Create simplified record
            mapped_aircraft = {
                "icao": aircraft.get("Designator", ""),
                "name": f"{manufacturer} {aircraft.get('ModelFullName', '')}".strip(),
            }
            landplane_aircraft.append(mapped_aircraft)

    # Sort by ICAO code for easier lookup
    landplane_aircraft.sort(key=lambda x: x["icao"])

    # Save filtered and mapped results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(landplane_aircraft, f, indent=2, ensure_ascii=False)

    # Print summary
    print(
        f"✓ Filtered {len(all_aircraft)} aircraft down to {len(landplane_aircraft)} LandPlane aircraft"
    )
    print(f"✓ Results saved to {output_file}")

    return landplane_aircraft


# if __name__ == "__main__":
#     # Filter and map the aircraft
#     landplane_aircraft = filter_and_map_landplane_aircraft()


# if __name__ == "__main__":
#     fetch_aircraft_types()
