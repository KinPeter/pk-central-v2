import pytest
from app.common.date_utils import (
    add_one_day,
    get_month_end,
    get_month_start,
    get_week_end,
    get_week_start,
    subtract_days,
    to_iso_day_end,
    to_iso_day_start,
)


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


class TestSubtractDays:
    def test_subtract_one_day(self):
        assert subtract_days("2024-01-15", 1) == "2024-01-14"

    def test_subtract_multiple_days(self):
        assert subtract_days("2024-01-15", 5) == "2024-01-10"

    def test_cross_month_boundary(self):
        assert subtract_days("2024-02-01", 1) == "2024-01-31"

    def test_cross_year_boundary(self):
        assert subtract_days("2025-01-01", 1) == "2024-12-31"

    def test_leap_year_february(self):
        assert subtract_days("2024-03-01", 1) == "2024-02-29"

    def test_non_leap_year_february(self):
        assert subtract_days("2023-03-01", 1) == "2023-02-28"

    def test_subtract_twenty_nine_days(self):
        assert subtract_days("2026-05-30", 29) == "2026-05-01"

    def test_invalid_date_raises_error(self):
        with pytest.raises(ValueError):
            subtract_days("2024-13-01", 1)

    def test_invalid_format_raises_error(self):
        with pytest.raises(ValueError):
            subtract_days("01-15-2024", 1)


class TestGetWeekStart:
    def test_monday_gives_same_day(self):
        assert get_week_start("2026-06-01") == "2026-06-01"

    def test_wednesday_gives_monday(self):
        assert get_week_start("2026-06-03") == "2026-06-01"

    def test_sunday_gives_previous_monday(self):
        assert get_week_start("2026-06-07") == "2026-06-01"

    def test_cross_month_boundary(self):
        assert get_week_start("2026-07-02") == "2026-06-29"

    def test_default_returns_string(self):
        result = get_week_start()
        assert isinstance(result, str)
        assert len(result) == 10


class TestGetWeekEnd:
    def test_monday_gives_sunday(self):
        assert get_week_end("2026-06-01") == "2026-06-07"

    def test_wednesday_gives_sunday(self):
        assert get_week_end("2026-06-03") == "2026-06-07"

    def test_sunday_gives_same_day(self):
        assert get_week_end("2026-06-07") == "2026-06-07"

    def test_cross_month_boundary(self):
        assert get_week_end("2026-07-02") == "2026-07-05"

    def test_default_returns_string(self):
        result = get_week_end()
        assert isinstance(result, str)
        assert len(result) == 10


class TestGetMonthStart:
    def test_mid_month(self):
        assert get_month_start("2026-06-15") == "2026-06-01"

    def test_first_of_month(self):
        assert get_month_start("2026-06-01") == "2026-06-01"

    def test_december(self):
        assert get_month_start("2026-12-25") == "2026-12-01"

    def test_default_returns_string(self):
        result = get_month_start()
        assert isinstance(result, str)
        assert len(result) == 10


class TestGetMonthEnd:
    def test_30_day_month(self):
        assert get_month_end("2026-04-15") == "2026-04-30"

    def test_31_day_month(self):
        assert get_month_end("2026-01-15") == "2026-01-31"

    def test_february_non_leap(self):
        assert get_month_end("2023-02-15") == "2023-02-28"

    def test_february_leap_year(self):
        assert get_month_end("2024-02-15") == "2024-02-29"

    def test_december(self):
        assert get_month_end("2026-12-25") == "2026-12-31"

    def test_default_returns_string(self):
        result = get_month_end()
        assert isinstance(result, str)
        assert len(result) == 10


class TestToIsoDayStart:
    def test_standard_date(self):
        assert to_iso_day_start("2026-06-09") == "2026-06-09T00:00:00+00:00"

    def test_edge_january(self):
        assert to_iso_day_start("2026-01-01") == "2026-01-01T00:00:00+00:00"


class TestToIsoDayEnd:
    def test_standard_date(self):
        assert to_iso_day_end("2026-06-09") == "2026-06-09T23:59:59.999999+00:00"

    def test_edge_january(self):
        assert to_iso_day_end("2026-01-01") == "2026-01-01T23:59:59.999999+00:00"
