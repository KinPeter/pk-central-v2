from dataclasses import dataclass
from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
from xml.etree import ElementTree as ET

from app.modules.activities.activities_types import ActivityData, ActivityType

# ---------------------------------------------------------------------------
# Constants / Thresholds
# ---------------------------------------------------------------------------

# Maximum plausible speed in m/s (~180 km/h) — anything above is a GPS glitch
MAX_PLAUSIBLE_SPEED_M_PER_S = 50.0

# Speed in m/s below which we consider the athlete to be stopped
# (~1.8 km/h — slower than walking pace)
STOP_SPEED_THRESHOLD_M_PER_S = 0.5

# Minimum distance per segment to accumulate toward total distance.
# Walking has smaller per-second steps (~1.5m at 5.5 km/h) than
# cycling/boating, so we use a tighter threshold for walking to avoid
# filtering out real movement.
MOVEMENT_DISTANCE_THRESHOLD_WALK_M = 1.0
MOVEMENT_DISTANCE_THRESHOLD_ELSE_M = 3.0

# Sliding window size in seconds for max speed computation.
# Walking data is recorded at ~1 Hz and has more GPS noise, so a longer
# window smooths out spikes. Cycling/boating use a tighter 5s window.
MAX_SPEED_WINDOW_WALK_S = 10
MAX_SPEED_WINDOW_ELSE_S = 5

# XML namespaces used by Strava GPX files
GPX_NS = "http://www.topografix.com/GPX/1/1"
GPXTPX_NS = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class TrackPoint:
    """A single trackpoint parsed from a GPX file."""

    lat: float
    lon: float
    elevation: float | None
    timestamp: datetime
    heartrate: int | None
    cadence: int | None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_strava_gpx(gpx_content: str, source_id: str) -> ActivityData:
    """
    Parse a Strava GPX string into a fully computed ActivityData object.

    Args:
        gpx_content: The full text content of a GPX file.
        source_id: The external activity ID to attach.

    Returns:
        An ActivityData with all metrics computed from the track points.

    Raises:
        ValueError: If no track points are found in the GPX.
    """
    root = ET.fromstring(gpx_content)
    track_points = _extract_track_points(root)
    activity_type = _map_activity_type(root)
    name = _extract_name(root)

    if not track_points:
        raise ValueError("No track points found in GPX file")

    # Ensure chronological order
    track_points.sort(key=lambda point: point.timestamp)

    start_date = _format_timestamp(track_points[0].timestamp)
    elapsed_time = int(
        (track_points[-1].timestamp - track_points[0].timestamp).total_seconds()
    )

    # Heart rate stats across all points (not just moving ones)
    heartrate_values = [
        point.heartrate for point in track_points if point.heartrate is not None
    ]
    average_heartrate, max_heartrate = _compute_heartrate_stats(heartrate_values)

    # Cadence stats — exclude 0 (stopped, not pedalling) but include all
    # non-zero values regardless of movement state
    cadence_values = [
        point.cadence
        for point in track_points
        if point.cadence is not None and point.cadence > 0
    ]
    average_cadence, max_cadence = _compute_cadence_stats(cadence_values)

    # Thresholds depend on activity type
    if activity_type == ActivityType.WALK:
        min_distance_threshold = MOVEMENT_DISTANCE_THRESHOLD_WALK_M
        max_speed_window = MAX_SPEED_WINDOW_WALK_S
    else:
        min_distance_threshold = MOVEMENT_DISTANCE_THRESHOLD_ELSE_M
        max_speed_window = MAX_SPEED_WINDOW_ELSE_S

    # --- Movement metrics (per-segment pass) ---
    total_distance = 0.0
    moving_time = 0
    total_elevation_gain = 0.0

    # Track cumulative time and distance through *moving* segments for the
    # sliding-window max speed calculation later
    cumulative_times: list[float] = [0.0]
    cumulative_distances: list[float] = [0.0]

    for i in range(len(track_points) - 1):
        first = track_points[i]
        second = track_points[i + 1]

        time_delta = (second.timestamp - first.timestamp).total_seconds()
        if time_delta <= 0:
            continue

        distance = _haversine(first.lat, first.lon, second.lat, second.lon)
        speed = distance / time_delta

        # GPS glitch — implausibly high speed, skip the segment entirely
        if speed > MAX_PLAUSIBLE_SPEED_M_PER_S:
            continue

        # Stopped (speed too slow for meaningful movement)
        if speed < STOP_SPEED_THRESHOLD_M_PER_S:
            continue

        # Accumulate moving time (all segments that pass the filters above)
        moving_time += int(time_delta)

        # GPS drift while stationary — time counts but distance doesn't
        if distance < min_distance_threshold:
            continue

        total_distance += distance

        # Track cumulative stats for the sliding-window max speed
        cumulative_times.append(cumulative_times[-1] + time_delta)
        cumulative_distances.append(cumulative_distances[-1] + distance)

        # Accumulate positive elevation changes
        if first.elevation is not None and second.elevation is not None:
            elevation_gain = second.elevation - first.elevation
            if elevation_gain > 0:
                total_elevation_gain += elevation_gain

    # --- Max speed (sliding window) ---
    max_speed = _compute_max_speed_sliding_window(
        cumulative_times, cumulative_distances, max_speed_window
    )

    average_speed = total_distance / moving_time if moving_time > 0 else 0.0

    return ActivityData(
        type=activity_type,
        source_id=source_id,
        name=name,
        start_date=start_date,
        moving_time=moving_time,
        elapsed_time=elapsed_time,
        distance=round(total_distance, 2),
        total_elevation_gain=round(total_elevation_gain, 2),
        average_speed=round(average_speed, 4),
        max_speed=round(max_speed, 4),
        average_heartrate=average_heartrate,
        max_heartrate=max_heartrate,
        average_cadence=average_cadence,
        max_cadence=max_cadence,
    )


# ---------------------------------------------------------------------------
# XML parsing helpers
# ---------------------------------------------------------------------------


def _extract_track_points(root: ET.Element) -> list[TrackPoint]:
    """Extract all track points from the GPX XML tree."""
    points: list[TrackPoint] = []

    for trkpt in root.iter(f"{{{GPX_NS}}}trkpt"):
        lat = float(trkpt.get("lat", "0"))
        lon = float(trkpt.get("lon", "0"))

        elevation = _parse_optional_float(trkpt, f"{{{GPX_NS}}}ele")
        timestamp = _parse_timestamp(trkpt, f"{{{GPX_NS}}}time")

        heartrate = _parse_extension_int(trkpt, "hr")
        cadence = _parse_extension_int(trkpt, "cad")

        points.append(
            TrackPoint(
                lat=lat,
                lon=lon,
                elevation=elevation,
                timestamp=timestamp,
                heartrate=heartrate,
                cadence=cadence,
            )
        )

    return points


def _extract_name(root: ET.Element) -> str:
    """Extract the activity name from <trk><name>."""
    name_element = root.find(f".//{{{GPX_NS}}}trk/{{{GPX_NS}}}name")
    if name_element is not None and name_element.text:
        return name_element.text.strip()
    return ""


def _map_activity_type(root: ET.Element) -> ActivityType:
    """Map the GPX <trk><type> string to an ActivityType enum value."""
    type_element = root.find(f".//{{{GPX_NS}}}trk/{{{GPX_NS}}}type")
    gpx_type = (
        type_element.text.strip().lower()
        if type_element is not None and type_element.text
        else ""
    )

    if gpx_type == "walking":
        return ActivityType.WALK
    if gpx_type == "cycling":
        return ActivityType.RIDE
    # Everything else (Sailing, Sail, boating, unknown) → BOATING
    return ActivityType.BOATING


def _parse_optional_float(parent: ET.Element, tag: str) -> float | None:
    """Parse a float from an element's text, returning None if missing."""
    element = parent.find(tag)
    if element is not None and element.text:
        try:
            return float(element.text.strip())
        except ValueError:
            return None
    return None


def _parse_timestamp(parent: ET.Element, tag: str) -> datetime:
    """
    Parse an ISO 8601 timestamp from an element.

    Falls back to datetime.min if the element is missing (shouldn't happen
    in a valid GPX file, but provides a safe default).
    """
    element = parent.find(tag)
    if element is not None and element.text:
        cleaned = element.text.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    return datetime.min.replace(tzinfo=timezone.utc)


def _format_timestamp(dt: datetime) -> str:
    """Format a datetime as an ISO 8601 string."""
    return dt.isoformat()


def _parse_extension_int(parent: ET.Element, tag: str) -> int | None:
    """
    Parse an integer from a Garmin TrackPointExtension sub-element.
    Returns None if the tag doesn't exist or has no text.
    """
    element = parent.find(f".//{{{GPXTPX_NS}}}{tag}")
    if element is not None and element.text:
        try:
            return int(element.text.strip())
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the great-circle distance in meters between two lat/lon points
    using the Haversine formula.
    """
    earth_radius_m = 6_371_000

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))

    return earth_radius_m * c


def _compute_max_speed_sliding_window(
    cumulative_times: list[float],
    cumulative_distances: list[float],
    window_seconds: int,
) -> float:
    """
    Compute the maximum average speed over any sliding time window.

    Uses a two-pointer approach over the cumulative time/distance arrays
    so each window spans approximately *window_seconds* of moving time.
    This smooths out GPS jitter while preserving real acceleration bursts.
    """
    max_speed = 0.0
    end_pointer = 0

    for start_pointer in range(len(cumulative_times)):
        # Advance end_pointer until the window is at least window_seconds wide
        while (
            end_pointer < len(cumulative_times)
            and cumulative_times[end_pointer] - cumulative_times[start_pointer]
            < window_seconds
        ):
            end_pointer += 1

        if end_pointer < len(cumulative_times):
            window_time = (
                cumulative_times[end_pointer] - cumulative_times[start_pointer]
            )
            if window_time > 0:
                window_distance = (
                    cumulative_distances[end_pointer]
                    - cumulative_distances[start_pointer]
                )
                speed = window_distance / window_time
                if speed > max_speed:
                    max_speed = speed

    return max_speed


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------


def _compute_heartrate_stats(
    values: list[int],
) -> tuple[float | None, float | None]:
    """Return (average, max) heartrate, or (None, None) if no data."""
    if not values:
        return None, None
    return round(sum(values) / len(values), 1), float(max(values))


def _compute_cadence_stats(
    values: list[int],
) -> tuple[float | None, float | None]:
    """Return (average, max) cadence, or (None, None) if no data."""
    if not values:
        return None, None
    return round(sum(values) / len(values), 1), float(max(values))
