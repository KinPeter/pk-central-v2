from datetime import datetime, timedelta, timezone


def add_one_day(date_str: str) -> str:
    """
    Add one day to a date string in the format "YYYY-MM-DD"
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return (dt + timedelta(days=1)).strftime("%Y-%m-%d")


def subtract_days(date_str: str, days: int) -> str:
    """
    Subtract a number of days from a date string in the format "YYYY-MM-DD"
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return (dt - timedelta(days=days)).strftime("%Y-%m-%d")


def get_week_start(date_str: str | None = None) -> str:
    """
    Return the Monday of the week containing the given date (YYYY-MM-DD).
    If no date is given, uses the current UTC date.
    """
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now(timezone.utc)
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")


def get_week_end(date_str: str | None = None) -> str:
    """
    Return the Sunday of the week containing the given date (YYYY-MM-DD).
    If no date is given, uses the current UTC date.
    """
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now(timezone.utc)
    sunday = dt + timedelta(days=6 - dt.weekday())
    return sunday.strftime("%Y-%m-%d")


def get_month_start(date_str: str | None = None) -> str:
    """
    Return the first day of the month for the given date (YYYY-MM-DD).
    If no date is given, uses the current UTC date.
    """
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now(timezone.utc)
    return dt.replace(day=1).strftime("%Y-%m-%d")


def get_month_end(date_str: str | None = None) -> str:
    """
    Return the last day of the month for the given date (YYYY-MM-DD).
    If no date is given, uses the current UTC date.
    """
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now(timezone.utc)
    # Jump to the next month (day 28 always exists, then add 4 days)
    next_month = dt.replace(day=28) + timedelta(days=4)
    month_end = next_month - timedelta(days=next_month.day)
    return month_end.strftime("%Y-%m-%d")


def to_iso_day_start(date_str: str) -> str:
    """Convert a YYYY-MM-DD date string to an ISO start-of-day timestamp."""
    return f"{date_str}T00:00:00+00:00"


def to_iso_day_end(date_str: str) -> str:
    """Convert a YYYY-MM-DD date string to an ISO end-of-day timestamp."""
    return f"{date_str}T23:59:59.999999+00:00"
