import pytest
from app.common.date_utils import add_one_day


class TestAddOneDay:
    def test_normal_date(self):
        assert add_one_day("2024-01-15") == "2024-01-16"

    def test_cross_month_boundary(self):
        assert add_one_day("2024-01-31") == "2024-02-01"

    def test_cross_year_boundary(self):
        assert add_one_day("2024-12-31") == "2025-01-01"

    def test_leap_year_february(self):
        assert add_one_day("2024-02-28") == "2024-02-29"

    def test_leap_year_february_end(self):
        assert add_one_day("2024-02-29") == "2024-03-01"

    def test_non_leap_year_february(self):
        assert add_one_day("2023-02-28") == "2023-03-01"

    def test_invalid_date_raises_error(self):
        with pytest.raises(ValueError):
            add_one_day("2024-13-01")

    def test_invalid_format_raises_error(self):
        with pytest.raises(ValueError):
            add_one_day("01-15-2024")
