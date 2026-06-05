"""Unit tests for gpx_utils.py — covers all public and private functions."""

from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import pytest

from app.modules.activities.activities_types import ActivityType
from app.modules.activities.gpx_utils import (
    _compute_cadence_stats,
    _compute_heartrate_stats,
    _compute_max_speed_sliding_window,
    _extract_name,
    _extract_track_points,
    _format_timestamp,
    _haversine,
    _map_activity_type,
    _parse_extension_int,
    _parse_optional_float,
    _parse_timestamp,
    parse_strava_gpx,
)

# ---------------------------------------------------------------------------
# Test helpers: GPX builders
# ---------------------------------------------------------------------------


def _gpx_header() -> list[str]:
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="StravaGPX"',
        '  xmlns="http://www.topografix.com/GPX/1/1"',
        '  xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">',
    ]


def _gpx_footer() -> list[str]:
    return ["</gpx>"]


def _trk_element(name: str, type_: str) -> list[str]:
    return [
        "  <trk>",
        f"    <name>{name}</name>",
        f"    <type>{type_}</type>",
        "    <trkseg>",
    ]


def _trk_end() -> list[str]:
    return ["    </trkseg>", "  </trk>"]


def _trkpt(
    lat: float,
    lon: float,
    ele: float | None = None,
    time_str: str | None = None,
    hr: int | None = None,
    cad: int | None = None,
) -> list[str]:
    lines = [f'      <trkpt lat="{lat}" lon="{lon}">']
    if ele is not None:
        lines.append(f"        <ele>{ele}</ele>")
    if time_str is not None:
        lines.append(f"        <time>{time_str}</time>")
    if hr is not None or cad is not None:
        lines.append("        <extensions>")
        lines.append("          <gpxtpx:TrackPointExtension>")
        if hr is not None:
            lines.append(f"            <gpxtpx:hr>{hr}</gpxtpx:hr>")
        if cad is not None:
            lines.append(f"            <gpxtpx:cad>{cad}</gpxtpx:cad>")
        lines.append("          </gpxtpx:TrackPointExtension>")
        lines.append("        </extensions>")
    lines.append("      </trkpt>")
    return lines


def _build_gpx(
    name: str,
    type_: str,
    points: list[dict],
) -> str:
    """Build a complete GPX XML string from structured data."""
    lines: list[str] = []
    lines.extend(_gpx_header())
    lines.extend(_trk_element(name, type_))
    for pt in points:
        lines.extend(_trkpt(**pt))
    lines.extend(_trk_end())
    lines.extend(_gpx_footer())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

# 3 track points for a simple walking scenario, 10 seconds apart.
# P0 → P1 ≈ ~111m, P1 → P2 ≈ ~111m  (at 0.001° lat spacing)
WALK_POINTS = [
    dict(
        lat=51.5, lon=-0.13, ele=10.0, time_str="2024-06-01T12:00:00Z", hr=120, cad=80
    ),
    dict(
        lat=51.501, lon=-0.13, ele=10.5, time_str="2024-06-01T12:00:10Z", hr=125, cad=82
    ),
    dict(
        lat=51.502, lon=-0.13, ele=11.0, time_str="2024-06-01T12:00:20Z", hr=130, cad=84
    ),
]

WALK_GPX = _build_gpx("Morning Walk", "walking", WALK_POINTS)

SAMPLE_DISTANCE_01 = _haversine(51.5, -0.13, 51.501, -0.13)
SAMPLE_DISTANCE_12 = _haversine(51.501, -0.13, 51.502, -0.13)


# ===================================================================
# Private helper tests
# ===================================================================


class TestHaversine:
    def test_zero_distance(self):
        assert _haversine(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_known_distance(self):
        # 1° of latitude ≈ 111_320 m
        dist = _haversine(51.5, -0.13, 51.501, -0.13)
        assert 100 < dist < 120  # ~111 m

    def test_symmetric(self):
        d1 = _haversine(10.0, 20.0, 30.0, 40.0)
        d2 = _haversine(30.0, 40.0, 10.0, 20.0)
        assert abs(d1 - d2) < 0.001


class TestParseOptionalFloat:
    def test_present(self):
        xml = "<root><ele>42.5</ele></root>"
        root = ET.fromstring(xml)
        assert _parse_optional_float(root, "ele") == 42.5

    def test_missing(self):
        xml = "<root><foo>bar</foo></root>"
        root = ET.fromstring(xml)
        assert _parse_optional_float(root, "ele") is None

    def test_empty_text(self):
        xml = "<root><ele></ele></root>"
        root = ET.fromstring(xml)
        assert _parse_optional_float(root, "ele") is None

    def test_invalid_value(self):
        xml = "<root><ele>not-a-number</ele></root>"
        root = ET.fromstring(xml)
        assert _parse_optional_float(root, "ele") is None


class TestParseTimestamp:
    def test_z_suffix(self):
        xml = "<root><time>2024-06-01T12:00:00Z</time></root>"
        root = ET.fromstring(xml)
        result = _parse_timestamp(root, "time")
        assert result == datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_offset_suffix(self):
        xml = "<root><time>2024-06-01T12:00:00+00:00</time></root>"
        root = ET.fromstring(xml)
        result = _parse_timestamp(root, "time")
        assert result == datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_missing(self):
        xml = "<root><foo>bar</foo></root>"
        root = ET.fromstring(xml)
        result = _parse_timestamp(root, "time")
        assert result == datetime.min.replace(tzinfo=timezone.utc)

    def test_empty_text(self):
        xml = "<root><time></time></root>"
        root = ET.fromstring(xml)
        result = _parse_timestamp(root, "time")
        assert result == datetime.min.replace(tzinfo=timezone.utc)


class TestFormatTimestamp:
    def test_format_utc(self):
        dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert _format_timestamp(dt) == "2024-06-01T12:00:00+00:00"


class TestParseExtensionInt:
    def test_hr_present(self):
        xml = """<trkpt lat="0" lon="0">
          <extensions>
            <gpxtpx:TrackPointExtension
              xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
              <gpxtpx:hr>150</gpxtpx:hr>
            </gpxtpx:TrackPointExtension>
          </extensions>
        </trkpt>"""
        root = ET.fromstring(xml)
        assert _parse_extension_int(root, "hr") == 150

    def test_cad_present(self):
        xml = """<trkpt lat="0" lon="0">
          <extensions>
            <gpxtpx:TrackPointExtension
              xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
              <gpxtpx:cad>85</gpxtpx:cad>
            </gpxtpx:TrackPointExtension>
          </extensions>
        </trkpt>"""
        root = ET.fromstring(xml)
        assert _parse_extension_int(root, "cad") == 85

    def test_missing_tag(self):
        xml = """<trkpt lat="0" lon="0">
          <extensions>
            <gpxtpx:TrackPointExtension
              xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
            </gpxtpx:TrackPointExtension>
          </extensions>
        </trkpt>"""
        root = ET.fromstring(xml)
        assert _parse_extension_int(root, "hr") is None

    def test_no_extensions(self):
        xml = '<trkpt lat="0" lon="0"></trkpt>'
        root = ET.fromstring(xml)
        assert _parse_extension_int(root, "hr") is None

    def test_invalid_value(self):
        xml = """<trkpt lat="0" lon="0">
          <extensions>
            <gpxtpx:TrackPointExtension
              xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
              <gpxtpx:hr>not-a-number</gpxtpx:hr>
            </gpxtpx:TrackPointExtension>
          </extensions>
        </trkpt>"""
        root = ET.fromstring(xml)
        assert _parse_extension_int(root, "hr") is None


class TestExtractName:
    def test_name_present(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk><name>My Ride</name></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        assert _extract_name(root) == "My Ride"

    def test_name_missing(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        assert _extract_name(root) == ""

    def test_name_empty(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk><name></name></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        assert _extract_name(root) == ""


class TestMapActivityType:
    def test_walking(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk><type>walking</type></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        assert _map_activity_type(root) == ActivityType.WALK

    def test_cycling(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk><type>cycling</type></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        assert _map_activity_type(root) == ActivityType.RIDE

    def test_sailing(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk><type>Sailing</type></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        assert _map_activity_type(root) == ActivityType.BOATING

    def test_boating(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk><type>boating</type></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        assert _map_activity_type(root) == ActivityType.BOATING

    def test_unknown_type_falls_to_boating(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk><type>running</type></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        # Unrecognized types default to BOATING
        assert _map_activity_type(root) == ActivityType.BOATING

    def test_missing_type(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        assert _map_activity_type(root) == ActivityType.BOATING

    def test_case_insensitive(self):
        xml = """<gpx xmlns="http://www.topografix.com/GPX/1/1">
          <trk><type>Walking</type></trk>
        </gpx>"""
        root = ET.fromstring(xml)
        assert _map_activity_type(root) == ActivityType.WALK


class TestComputeHeartrateStats:
    def test_with_values(self):
        avg, mx = _compute_heartrate_stats([120, 130, 140])
        assert avg == 130.0
        assert mx == 140.0

    def test_empty(self):
        avg, mx = _compute_heartrate_stats([])
        assert avg is None
        assert mx is None

    def test_single_value(self):
        avg, mx = _compute_heartrate_stats([150])
        assert avg == 150.0
        assert mx == 150.0


class TestComputeCadenceStats:
    def test_with_values(self):
        avg, mx = _compute_cadence_stats([80, 85, 90])
        assert avg == 85.0
        assert mx == 90.0

    def test_empty(self):
        avg, mx = _compute_cadence_stats([])
        assert avg is None
        assert mx is None

    def test_single_value(self):
        avg, mx = _compute_cadence_stats([75])
        assert avg == 75.0
        assert mx == 75.0


class TestComputeMaxSpeedSlidingWindow:
    def test_constant_speed(self):
        # 3 points, each 10s apart, equal distance steps
        times = [0.0, 10.0, 20.0]
        dists = [0.0, 100.0, 200.0]
        speed = _compute_max_speed_sliding_window(times, dists, 5)
        # 5s window covers the first 100m in 10s → 10 m/s
        assert speed == 10.0

    def test_single_segment(self):
        times = [0.0, 5.0]
        dists = [0.0, 50.0]
        speed = _compute_max_speed_sliding_window(times, dists, 3)
        assert speed == 10.0

    def test_two_points_only(self):
        times = [0.0, 10.0]
        dists = [0.0, 100.0]
        speed = _compute_max_speed_sliding_window(times, dists, 5)
        # Window fits within the time span → should detect the full speed
        assert speed == 10.0

    def test_no_movement(self):
        times = [0.0, 10.0, 20.0]
        dists = [0.0, 0.0, 0.0]
        speed = _compute_max_speed_sliding_window(times, dists, 5)
        assert speed == 0.0


class TestExtractTrackPoints:
    def test_extracts_all_points(self):
        xml = _build_gpx("Test", "walking", WALK_POINTS)
        root = ET.fromstring(xml)
        points = _extract_track_points(root)

        assert len(points) == 3

        assert points[0].lat == 51.5
        assert points[0].lon == -0.13
        assert points[0].elevation == 10.0
        assert points[0].heartrate == 120
        assert points[0].cadence == 80
        assert points[0].timestamp == datetime(
            2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc
        )

        assert points[1].lat == 51.501
        assert points[2].lat == 51.502

    def test_empty_gpx(self):
        xml = _build_gpx("Empty", "walking", [])
        root = ET.fromstring(xml)
        points = _extract_track_points(root)
        assert points == []

    def test_points_without_extras(self):
        points_data = [
            dict(lat=0.0, lon=0.0, time_str="2024-01-01T00:00:00Z"),
            dict(lat=0.001, lon=0.0, time_str="2024-01-01T00:00:10Z"),
        ]
        xml = _build_gpx("No extras", "walking", points_data)
        root = ET.fromstring(xml)
        points = _extract_track_points(root)

        assert len(points) == 2
        assert points[0].elevation is None
        assert points[0].heartrate is None
        assert points[0].cadence is None


# ===================================================================
# Main function: parse_strava_gpx
# ===================================================================


class TestParseStravaGpx:
    def test_basic_walk(self):
        """A simple 3-point walk produces correct metrics."""
        result = parse_strava_gpx(WALK_GPX, "src_001")

        assert result.type == ActivityType.WALK
        assert result.source_id == "src_001"
        assert result.name == "Morning Walk"
        assert result.start_date == "2024-06-01T12:00:00+00:00"

        # Elapsed time: 20s (12:00:00 → 12:00:20)
        assert result.elapsed_time == 20
        # Moving time: all 20s (no glitches, no stopping)
        assert result.moving_time == 20

        # Distance: sum of the two segments
        expected_distance = SAMPLE_DISTANCE_01 + SAMPLE_DISTANCE_12
        assert result.distance == pytest.approx(expected_distance, rel=1e-4)

        # Elevation gain: (10.5-10.0) + (11.0-10.5) = 1.0
        assert result.total_elevation_gain == 1.0

        # Average speed: distance / moving_time
        expected_avg_speed = expected_distance / 20
        assert result.average_speed == pytest.approx(expected_avg_speed, rel=1e-4)

        # Max speed: sliding window of 10s across 2 segments
        assert result.max_speed > 0

        # Heartrate
        assert result.average_heartrate == pytest.approx(125.0, rel=1e-4)
        assert result.max_heartrate == 130.0

        # Cadence
        assert result.average_cadence == pytest.approx(82.0, rel=1e-4)
        assert result.max_cadence == 84.0

    def test_cycling(self):
        """Cycling GPX produces RIDE type."""
        points = [
            dict(lat=51.5, lon=-0.13, ele=10.0, time_str="2024-06-01T12:00:00Z"),
            dict(lat=51.505, lon=-0.13, ele=10.0, time_str="2024-06-01T12:00:10Z"),
            dict(lat=51.510, lon=-0.13, ele=10.0, time_str="2024-06-01T12:00:20Z"),
        ]
        gpx = _build_gpx("Bike Ride", "cycling", points)
        result = parse_strava_gpx(gpx, "src_002")

        assert result.type == ActivityType.RIDE
        assert result.name == "Bike Ride"
        assert result.elapsed_time == 20

    def test_boating(self):
        """Sailing GPX produces BOATING type."""
        points = [
            dict(lat=51.5, lon=-0.13, time_str="2024-06-01T12:00:00Z"),
            dict(lat=51.51, lon=-0.13, time_str="2024-06-01T12:00:10Z"),
        ]
        gpx = _build_gpx("Sail Trip", "Sailing", points)
        result = parse_strava_gpx(gpx, "src_003")

        assert result.type == ActivityType.BOATING

    def test_no_track_points_raises(self):
        """GPX with no track points raises ValueError."""
        gpx = _build_gpx("Empty", "walking", [])
        with pytest.raises(ValueError, match="No track points found"):
            parse_strava_gpx(gpx, "src_004")

    def test_no_heartrate_or_cadence(self):
        """Points without HR/cadence produce None stats."""
        points = [
            dict(lat=51.5, lon=-0.13, time_str="2024-06-01T12:00:00Z"),
            dict(lat=51.501, lon=-0.13, time_str="2024-06-01T12:00:10Z"),
        ]
        gpx = _build_gpx("No HR", "walking", points)
        result = parse_strava_gpx(gpx, "src_005")

        assert result.average_heartrate is None
        assert result.max_heartrate is None
        assert result.average_cadence is None
        assert result.max_cadence is None

    def test_gps_glitch_filtered(self):
        """A segment with implausibly high speed is skipped."""
        # Point 1 → Point 2: huge lat jump in 1s → GPS glitch
        points = [
            dict(lat=51.5, lon=-0.13, ele=10.0, time_str="2024-06-01T12:00:00Z"),
            dict(lat=52.0, lon=-0.13, ele=10.0, time_str="2024-06-01T12:00:01Z"),
            # 0.5° in 1s ≈ 55 km → 55_000 m/s, well over MAX_PLAUSIBLE_SPEED_M_PER_S (50)
            dict(lat=52.001, lon=-0.13, ele=10.0, time_str="2024-06-01T12:00:11Z"),
            # Last two at normal speed: 0.001° in 10s ≈ 11 m/s
        ]
        gpx = _build_gpx("Glitchy", "walking", points)

        result = parse_strava_gpx(gpx, "src_006")

        # Only the last segment (P2→P3) should count
        expected_distance = _haversine(52.0, -0.13, 52.001, -0.13)
        assert result.distance == pytest.approx(expected_distance, rel=1e-4)
        # Moving time = 10s (only the clean segment)
        assert result.moving_time == 10
        # Elapsed time = 11s (total span P0→P3)
        assert result.elapsed_time == 11

    def test_stopped_segments_filtered(self):
        """Segments below STOP_SPEED_THRESHOLD are filtered out."""
        # Very small lat movement → speed well below 0.5 m/s
        points = [
            dict(lat=51.5, lon=-0.13, time_str="2024-06-01T12:00:00Z"),
            dict(lat=51.5, lon=-0.13, time_str="2024-06-01T12:00:10Z"),
            # Same location → 0 distance → below threshold
            dict(lat=51.500001, lon=-0.13, time_str="2024-06-01T12:00:20Z"),
            # ~0.1m in 10s → 0.01 m/s, well below 0.5
        ]
        gpx = _build_gpx("Stopped", "walking", points)
        result = parse_strava_gpx(gpx, "src_007")

        # No meaningful movement should be recorded
        assert result.distance == 0.0
        assert result.moving_time == 0

    def test_gps_drift_filtered(self):
        """Segments below the movement distance threshold contribute
        time but not distance."""
        # Very tiny movement — below MOVEMENT_DISTANCE_THRESHOLD_WALK_M (1.0m)
        # 0.000001° lat ≈ 0.11m in 10s → speed ~0.011 m/s, which is
        # below STOP_SPEED_THRESHOLD_M_PER_S (0.5). So it'll be stopped.
        # Let's make it slightly faster but still under 1m distance.
        # 0.000005° lat ≈ 0.55m in 10s → speed ~0.055 m/s, still below 0.5 m/s.
        # Hmm, trickier. Let's make it faster but very short distance.
        # 0.000008° lat ≈ 0.89m in 1s → speed ~0.89 m/s (above 0.5, so not stopped)
        # but distance 0.89m < 1.0m walk threshold.
        points = [
            dict(lat=51.5, lon=-0.13, time_str="2024-06-01T12:00:00Z"),
            dict(lat=51.500008, lon=-0.13, time_str="2024-06-01T12:00:01Z"),
            # ~0.89m in 1s → speed ~0.89 m/s > 0.5, but distance < 1.0m walk threshold
            dict(lat=51.500016, lon=-0.13, time_str="2024-06-01T12:00:02Z"),
            # Another ~0.89m
        ]
        gpx = _build_gpx("Drifting", "walking", points)
        result = parse_strava_gpx(gpx, "src_008")

        # Time should accumulate (speed > STOP_SPEED_THRESHOLD)
        assert result.moving_time > 0
        # But distance should NOT accumulate (below movement threshold)
        assert result.distance == 0.0

    def test_chronological_sort(self):
        """Track points are sorted by timestamp regardless of input order."""
        points = [
            dict(lat=51.51, lon=-0.13, time_str="2024-06-01T12:00:20Z"),
            dict(lat=51.50, lon=-0.13, time_str="2024-06-01T12:00:00Z"),
            dict(lat=51.505, lon=-0.13, time_str="2024-06-01T12:00:10Z"),
        ]
        gpx = _build_gpx("Unsorted", "walking", points)
        result = parse_strava_gpx(gpx, "src_009")

        # Start date should be the earliest timestamp
        assert result.start_date == "2024-06-01T12:00:00+00:00"
        assert result.elapsed_time == 20

    def test_single_track_point(self):
        """A single point with no segments produces zero metrics."""
        points = [
            dict(lat=51.5, lon=-0.13, time_str="2024-06-01T12:00:00Z"),
        ]
        gpx = _build_gpx("Single", "walking", points)
        result = parse_strava_gpx(gpx, "src_010")

        assert result.distance == 0.0
        assert result.moving_time == 0
        assert result.elapsed_time == 0
        assert result.max_speed == 0.0
        assert result.average_speed == 0.0
        assert result.total_elevation_gain == 0.0

    def test_cadence_excludes_zero(self):
        """Cadence values of 0 are excluded from stats."""
        points = [
            dict(lat=51.5, lon=-0.13, time_str="2024-06-01T12:00:00Z", cad=0),
            dict(lat=51.501, lon=-0.13, time_str="2024-06-01T12:00:05Z", cad=80),
            dict(lat=51.502, lon=-0.13, time_str="2024-06-01T12:00:10Z", cad=90),
        ]
        gpx = _build_gpx("Cad zeros", "cycling", points)
        result = parse_strava_gpx(gpx, "src_011")

        assert result.average_cadence == pytest.approx(85.0, rel=1e-4)
        assert result.max_cadence == 90.0

    def test_all_cadence_zero(self):
        """When all cadence values are 0, cadence stats are None."""
        points = [
            dict(lat=51.5, lon=-0.13, time_str="2024-06-01T12:00:00Z", cad=0),
            dict(lat=51.501, lon=-0.13, time_str="2024-06-01T12:00:05Z", cad=0),
        ]
        gpx = _build_gpx("All zero cad", "cycling", points)
        result = parse_strava_gpx(gpx, "src_012")

        assert result.average_cadence is None
        assert result.max_cadence is None

    def test_zero_time_delta_skipped(self):
        """Consecutive points with same timestamp are skipped (no division by zero)."""
        points = [
            dict(lat=51.5, lon=-0.13, time_str="2024-06-01T12:00:00Z"),
            dict(lat=51.501, lon=-0.13, time_str="2024-06-01T12:00:00Z"),
            # Same timestamp → time_delta = 0, should be skipped
            dict(lat=51.502, lon=-0.13, time_str="2024-06-01T12:00:10Z"),
            # Normal segment
        ]
        gpx = _build_gpx("Zero delta", "walking", points)
        result = parse_strava_gpx(gpx, "src_013")

        # Only the last segment should be counted
        expected_distance = _haversine(51.501, -0.13, 51.502, -0.13)
        assert result.distance == pytest.approx(expected_distance, rel=1e-4)
        assert result.moving_time == 10


# ===================================================================
# Integration tests — real GPX files
# ===================================================================


_TEST_FILES_DIR = "acceptance_tests/test_files"


class TestParseStravaGpxRealFiles:
    """Integration-style tests using real Strava GPX files.

    These tests verify that parse_strava_gpx produces consistent results
    on real-world data. Values are compared against a baseline with a
    tolerance to allow for minor algorithm changes (e.g. coordinate
    calculation improvements).
    """

    # Relative tolerances for computed fields
    REL_DISTANCE = 0.01
    REL_ELEVATION = 0.02
    REL_SPEED = 0.02
    REL_HR = 0.02
    REL_CADENCE = 0.02

    @staticmethod
    def _load_gpx(filename: str) -> str:
        path = f"{_TEST_FILES_DIR}/{filename}"
        with open(path) as f:
            return f.read()

    # --- walk.gpx ---

    def test_walk(self):
        result = parse_strava_gpx(self._load_gpx("walk.gpx"), "walk")

        assert result.type == ActivityType.WALK
        assert result.name == "Afternoon Walk"
        assert result.source_id == "walk"
        assert result.start_date == "2026-06-01T11:18:28+00:00"

        assert result.elapsed_time == 3026
        assert result.moving_time == 2857

        assert result.distance == pytest.approx(4445.63, rel=self.REL_DISTANCE)
        assert result.total_elevation_gain == pytest.approx(
            98.2, rel=self.REL_ELEVATION
        )

        assert result.average_speed == pytest.approx(1.556, rel=self.REL_SPEED)
        assert result.max_speed == pytest.approx(3.3042, rel=self.REL_SPEED)

        assert result.average_heartrate == pytest.approx(119.9, rel=self.REL_HR)
        assert result.max_heartrate == 136.0

        assert result.average_cadence == pytest.approx(52.3, rel=self.REL_CADENCE)
        assert result.max_cadence == 90.0

    # --- ride.gpx ---

    def test_ride(self):
        result = parse_strava_gpx(self._load_gpx("ride.gpx"), "ride")

        assert result.type == ActivityType.RIDE
        assert result.name == "Afternoon Ride"
        assert result.source_id == "ride"
        assert result.start_date == "2026-05-28T15:59:01+00:00"

        assert result.elapsed_time == 1091
        assert result.moving_time == 861

        assert result.distance == pytest.approx(4016.9, rel=self.REL_DISTANCE)
        assert result.total_elevation_gain == pytest.approx(
            18.2, rel=self.REL_ELEVATION
        )

        assert result.average_speed == pytest.approx(4.6654, rel=self.REL_SPEED)
        assert result.max_speed == pytest.approx(7.8051, rel=self.REL_SPEED)

        assert result.average_heartrate == pytest.approx(104.1, rel=self.REL_HR)
        assert result.max_heartrate == 122.0

        assert result.average_cadence == pytest.approx(81.1, rel=self.REL_CADENCE)
        assert result.max_cadence == 96.0

    # --- boating.gpx ---

    def test_boating(self):
        result = parse_strava_gpx(self._load_gpx("boating.gpx"), "boating")

        assert result.type == ActivityType.BOATING
        assert result.name == "Danube boating"
        assert result.source_id == "boating"
        assert result.start_date == "2026-05-23T08:12:58+00:00"

        assert result.elapsed_time == 6927
        assert result.moving_time == 6645

        assert result.distance == pytest.approx(39123.84, rel=self.REL_DISTANCE)
        assert result.total_elevation_gain == pytest.approx(
            209.6, rel=self.REL_ELEVATION
        )

        assert result.average_speed == pytest.approx(5.8877, rel=self.REL_SPEED)
        assert result.max_speed == pytest.approx(14.0172, rel=self.REL_SPEED)

        assert result.average_heartrate == pytest.approx(92.4, rel=self.REL_HR)
        assert result.max_heartrate == 161.0

        assert result.average_cadence is None
        assert result.max_cadence is None
