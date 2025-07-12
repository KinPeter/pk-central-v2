SIMPLE_DATE_REGEX = r"^([2-9]\d{3})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"
SIMPLE_DATE_REGEX_POSSIBLE_PAST = (
    r"^([2-9]\d{3}|19\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"
)
SIMPLE_TIME_REGEX = r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$"
MONTH_PER_DAY_REGEX = r"^(1[0-2]|0?[1-9])/(3[01]|[12][0-9]|0?[1-9])$"
YEAR_REGEX = r"^\d{4}$"
COORDINATES_QUERY_REGEX = r"^([-+]?\d{1,3}(?:\.\d+)?),\s*([-+]?\d{1,3}(?:\.\d+)?)$"
