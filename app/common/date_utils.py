from datetime import datetime, timedelta


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
