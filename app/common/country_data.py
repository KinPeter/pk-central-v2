import json
from pathlib import Path


class CountryData:
    """
    Class to handle country data, including names and continents.
    Uses a JSON file to store country information.
    """

    continents = {
        "AF": "Africa",
        "AN": "Antartica",
        "AS": "Asia",
        "EU": "Europe",
        "NA": "North America",
        "OC": "Oceania",
        "SA": "South America",
    }

    def __init__(self):
        project_root = Path(__file__).resolve().parents[2]
        self.countries_path = project_root / "app" / "static_data" / "countries.json"

    def get_name(self, country_code: str) -> str:
        """
        Get the name of the country by its code.
        """
        with open(self.countries_path, "r") as f:
            countries = json.load(f)
            country_code = country_code.upper()
            if country_code in countries:
                return countries[country_code]["name"]
            else:
                raise ValueError(f"Country {country_code} not found.")

    def get_continent(self, country_code: str) -> str:
        """
        Get the continent of the country by its code.
        """
        with open(self.countries_path, "r") as f:
            countries = json.load(f)
            country_code = country_code.upper()
            if country_code in countries:
                continent_code = countries[country_code]["continent"]
                return self.continents.get(continent_code, "Unknown")
            else:
                raise ValueError(f"Country {country_code} not found.")
