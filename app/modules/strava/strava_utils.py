from logging import Logger

from app.modules.strava.strava_types import Coords, StravaRoutemap


def generate_routemap(
    activities: list[dict], logger: Logger, sampling_rate: int = 5
) -> StravaRoutemap:
    """
    Generate a route map based on activity data.
    This function takes a list of activities, extracts route coordinates,
    and clusters them.

    ### Adjust this parameters to control clustering sensitivity and performance.
    - `sampling_rate`: How often to sample points from the route (e.g., every 5th point). Default is 5.
    """

    points: set[Coords] = set()
    activity_count = len(activities)

    for index, activity in enumerate(activities):
        route = activity["route"]
        if not route:
            continue

        logger.info(
            f"Processing activity {index+1}/{activity_count} {activity['strava_id']} with {len(route)} coordinates."
        )

        points_before = len(points)
        for entry in route[1::sampling_rate]:
            # Round coordinates to 4 decimal places for better clustering (approx. 11m precision)
            coords: Coords = (
                round(entry[0], 4),
                round(entry[1], 4),
            )
            points.add(coords)

        points_after = len(points)
        logger.info(
            f"Added {points_after - points_before} unique points from activity."
        )

    logger.info(f"Generated routemap with {len(points)} unique points.")

    return StravaRoutemap(points=points, count=len(points))
