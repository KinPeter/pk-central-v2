import pytest
from app.modules.birthdays.birthdays_utils import to_birthday
from app.modules.birthdays.birthdays_types import Birthday


@pytest.mark.parametrize(
    "data,expected",
    [
        # All fields present
        (
            {
                "id": "b1",
                "name": "Alice",
                "date": "1/12",
            },
            Birthday(
                id="b1",
                name="Alice",
                date="1/12",
            ),
        ),
        # Different date format
        (
            {
                "id": "b2",
                "name": "Bob",
                "date": "11/30",
            },
            Birthday(
                id="b2",
                name="Bob",
                date="11/30",
            ),
        ),
    ],
)
def test_to_birthday(data, expected):
    result = to_birthday(data)
    assert isinstance(result, Birthday)
    assert result.id == expected.id
    assert result.name == expected.name
    assert result.date == expected.date
