import pytest
from app.common.country_data import CountryData


class TestCountryData:
    @classmethod
    def setup_class(cls):
        cls.country_data = CountryData()

    def test_get_name_valid(self):
        assert self.country_data.get_name("DE") == "Germany"
        assert self.country_data.get_name("us") == "United States"
        assert self.country_data.get_name("IN") == "India"

    def test_get_name_invalid(self):
        with pytest.raises(ValueError) as excinfo:
            self.country_data.get_name("XX")
        assert "Country XX not found." in str(excinfo.value)

    def test_get_continent_valid(self):
        assert self.country_data.get_continent("DE") == "Europe"
        assert self.country_data.get_continent("US") == "North America"
        assert self.country_data.get_continent("IN") == "Asia"

    def test_get_continent_invalid(self):
        with pytest.raises(ValueError) as excinfo:
            self.country_data.get_continent("ZZ")
        assert "Country ZZ not found." in str(excinfo.value)

    def test_get_continent_unknown(self, monkeypatch):
        # Patch countries.json to return a country with an unknown continent code
        import json

        orig_path = self.country_data.countries_path
        with open(orig_path, "r") as f:
            countries = json.load(f)
        countries["XY"] = {"code3": "XYZ", "name": "Testland", "continent": "XX"}
        # Write to a temp file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            json.dump(countries, tmp)
            tmp_path = tmp.name
        monkeypatch.setattr(self.country_data, "countries_path", tmp_path)
        try:
            assert self.country_data.get_continent("XY") == "Unknown"
        finally:
            os.remove(tmp_path)
