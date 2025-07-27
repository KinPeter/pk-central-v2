import pytest
from unittest.mock import MagicMock
from app.modules.strava.strava_utils import generate_routemap
from app.modules.strava.strava_types import StravaRoutemap


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    return logger


@pytest.fixture
def sample_activities():
    # Clearer coordinates, first point in each route will be ignored by the algorithm
    return [
        {
            "strava_id": 1,
            "route": [
                [51.123456, -0.123456],  # ignored
                [51.234567, -0.234567],  # rounds to (51.2346, -0.2346)
                [51.345678, -0.345678],  # rounds to (51.3457, -0.3457)
                [51.456789, -0.456789],  # rounds to (51.4568, -0.4568)
                [51.567891, -0.567891],  # rounds to (51.5679, -0.5679)
            ],
        },
        {
            "strava_id": 2,
            "route": [
                [51.987654, -0.987654],  # ignored
                [51.234567, -0.234567],  # rounds to (51.2346, -0.2346), duplicate
                [51.876543, -0.876543],  # rounds to (51.8765, -0.8765)
                [51.345678, -0.345678],  # rounds to (51.3457, -0.3457), duplicate
                [51.999999, -0.999999],  # rounds to (52.0, -1.0)
            ],
        },
    ]


@pytest.fixture
def empty_activities():
    return []


@pytest.fixture
def activities_with_empty_route():
    return [
        {"strava_id": 1, "route": []},
        {"strava_id": 2, "route": None},
    ]


class TestGenerateRoutemap:
    def test_generate_routemap_basic(self, mock_logger, sample_activities):
        result = generate_routemap(
            sample_activities, logger=mock_logger, sampling_rate=1
        )
        assert isinstance(result, StravaRoutemap)
        # After skipping the first point in each route, rounding to 4 decimals, and removing duplicates:
        expected_points = {
            (51.2346, -0.2346),
            (51.3457, -0.3457),
            (51.4568, -0.4568),
            (51.5679, -0.5679),
            (51.8765, -0.8765),
            (52.0, -1.0),
        }
        assert result.points == expected_points
        assert result.count == len(expected_points)
        assert all(isinstance(pt, tuple) and len(pt) == 2 for pt in result.points)
        mock_logger.info.assert_any_call(
            f"Generated routemap with {len(expected_points)} unique points."
        )

    def test_generate_routemap_sampling(self, mock_logger, sample_activities):
        result = generate_routemap(
            sample_activities, logger=mock_logger, sampling_rate=2
        )
        # Should sample every 2nd point after the first, so for each route:
        # Route 1: [51.234567, -0.234567] (idx 1), [51.456789, -0.456789] (idx 3)
        # Route 2: [51.234567, -0.234567] (idx 1), [51.345678, -0.345678] (idx 3)
        # After rounding and removing duplicates:
        expected_points = {
            (51.2346, -0.2346),
            (51.4568, -0.4568),
            (51.3457, -0.3457),
        }
        assert result.points == expected_points
        assert result.count == len(expected_points)
        mock_logger.info.assert_any_call(
            f"Generated routemap with {len(expected_points)} unique points."
        )

    def test_generate_routemap_empty(self, mock_logger, empty_activities):
        result = generate_routemap(empty_activities, logger=mock_logger)
        assert isinstance(result, StravaRoutemap)
        assert result.count == 0
        assert result.points == set()
        mock_logger.info.assert_any_call("Generated routemap with 0 unique points.")

    def test_generate_routemap_empty_routes(
        self, mock_logger, activities_with_empty_route
    ):
        result = generate_routemap(activities_with_empty_route, logger=mock_logger)
        assert isinstance(result, StravaRoutemap)
        assert result.count == 0
        assert result.points == set()
        mock_logger.info.assert_any_call("Generated routemap with 0 unique points.")
