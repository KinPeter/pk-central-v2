import pytest
from datetime import datetime, timezone
from app.modules.visits.visits_utils import to_visit
from app.modules.visits.visits_types import Visit


@pytest.mark.parametrize(
    "item,expected",
    [
        # All fields present
        (
            {
                "id": "v1",
                "created_at": datetime(2025, 7, 12, tzinfo=timezone.utc),
                "city": "Paris",
                "country": "France",
                "lat": 48.8566,
                "lng": 2.3522,
                "year": "2023",
            },
            Visit(
                id="v1",
                created_at=datetime(2025, 7, 12, tzinfo=timezone.utc),
                city="Paris",
                country="France",
                lat=48.8566,
                lng=2.3522,
                year="2023",
            ),
        ),
        # Only required fields (year missing)
        (
            {
                "id": "v2",
                "created_at": datetime(2025, 7, 12, tzinfo=timezone.utc),
                "city": "London",
                "country": "UK",
                "lat": 51.5074,
                "lng": -0.1278,
                # year missing
            },
            Visit(
                id="v2",
                created_at=datetime(2025, 7, 12, tzinfo=timezone.utc),
                city="London",
                country="UK",
                lat=51.5074,
                lng=-0.1278,
                year=None,
            ),
        ),
        # Explicit year None
        (
            {
                "id": "v3",
                "created_at": datetime(2025, 7, 12, tzinfo=timezone.utc),
                "city": "Berlin",
                "country": "Germany",
                "lat": 52.52,
                "lng": 13.405,
                "year": None,
            },
            Visit(
                id="v3",
                created_at=datetime(2025, 7, 12, tzinfo=timezone.utc),
                city="Berlin",
                country="Germany",
                lat=52.52,
                lng=13.405,
                year=None,
            ),
        ),
    ],
)
def test_to_visit(item, expected):
    result = to_visit(item)
    assert isinstance(result, Visit)
    assert result.id == expected.id
    assert result.created_at == expected.created_at
    assert result.city == expected.city
    assert result.country == expected.country
    assert result.lat == expected.lat
    assert result.lng == expected.lng
    assert result.year == expected.year
