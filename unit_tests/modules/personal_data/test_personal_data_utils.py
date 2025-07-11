import pytest
from datetime import datetime, timezone
from app.modules.personal_data.personal_data_utils import to_personal_data
from app.modules.personal_data.personal_data_types import PersonalData


@pytest.mark.parametrize(
    "item,expected",
    [
        # All fields present
        (
            {
                "id": "p1",
                "created_at": datetime(2025, 7, 11, tzinfo=timezone.utc),
                "name": "Passport",
                "identifier": "123456789",
                "expiry": "2030-12-31",
            },
            PersonalData(
                id="p1",
                created_at=datetime(2025, 7, 11, tzinfo=timezone.utc),
                name="Passport",
                identifier="123456789",
                expiry="2030-12-31",
            ),
        ),
        # Only required fields
        (
            {
                "id": "p2",
                "created_at": datetime(2025, 7, 11, tzinfo=timezone.utc),
                "name": "ID Card",
                "identifier": "987654321",
                # expiry missing
            },
            PersonalData(
                id="p2",
                created_at=datetime(2025, 7, 11, tzinfo=timezone.utc),
                name="ID Card",
                identifier="987654321",
                expiry=None,
            ),
        ),
        # Explicit expiry None
        (
            {
                "id": "p3",
                "created_at": datetime(2025, 7, 11, tzinfo=timezone.utc),
                "name": "Driver License",
                "identifier": "A1B2C3D4",
                "expiry": None,
            },
            PersonalData(
                id="p3",
                created_at=datetime(2025, 7, 11, tzinfo=timezone.utc),
                name="Driver License",
                identifier="A1B2C3D4",
                expiry=None,
            ),
        ),
    ],
)
def test_to_personal_data(item, expected):
    result = to_personal_data(item)
    assert isinstance(result, PersonalData)
    assert result.id == expected.id
    assert result.created_at == expected.created_at
    assert result.name == expected.name
    assert result.identifier == expected.identifier
    assert result.expiry == expected.expiry
