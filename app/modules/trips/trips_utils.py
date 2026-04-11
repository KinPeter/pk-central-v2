import json
from datetime import datetime
from pathlib import Path

from app.modules.flights.flights_types import Flight
from app.modules.trips.trips_types import FlightMapData, FlightMapRoute, FlightStats, MapMarker, VisitMapData, VisitStats
from app.modules.visits.visits_types import Visit

_continents_path = Path(__file__).resolve().parents[3] / "app" / "static_data" / "continents.json"
with open(_continents_path, "r") as _f:
    CONTINENTS_FOR_COUNTRIES: dict[str, str] = json.load(_f)

MONTH_NAMES: dict[int, str] = {
    0: "January",
    1: "February",
    2: "March",
    3: "April",
    4: "May",
    5: "June",
    6: "July",
    7: "August",
    8: "September",
    9: "October",
    10: "November",
    11: "December",
}

DAY_NAMES: dict[int, str] = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
}


def compute_flights_stats(all_flights: list[Flight], years_filter: list[str] | None = None) -> FlightStats:
    flights = [f for f in all_flights if not f.is_planned]

    if not flights:
        empty_weekdays = [(DAY_NAMES[i], 0) for i in range(7)]
        # shift Sunday to end so Monday is first
        empty_weekdays.append(empty_weekdays.pop(0))
        return FlightStats(
            total_count=0,
            domestic_count=0,
            intl_count=0,
            total_distance=0,
            total_duration_minutes=0,
            flight_classes_by_count=[],
            reasons_by_count=[],
            seat_type_by_count=[],
            continents_by_count=[],
            total_countries=0,
            countries_by_count=[],
            total_airports=0,
            airports_by_count=[],
            total_airlines=0,
            airlines_by_count=[],
            airlines_by_distance=[],
            total_aircrafts=0,
            aircraft_by_count=[],
            aircraft_by_distance=[],
            total_routes=0,
            routes_by_count=[],
            routes_by_distance=[],
            flights_per_year=[],
            distance_per_year=[],
            flights_per_month=[(MONTH_NAMES[i], 0) for i in range(12)],
            flights_per_weekday=empty_weekdays,
            airports_map={},
            airlines_map={},
            aircraft_map={},
            years=[],
        )

    domestic_count = 0
    intl_count = 0
    total_distance: float = 0
    total_duration_minutes = 0
    flight_classes_count: dict[str, int] = {}
    reasons_count: dict[str, int] = {}
    seat_type_count: dict[str, int] = {}
    continents_count: dict[str, int] = {}
    countries_set: set[str] = set()
    countries_count: dict[str, int] = {}
    airports_map: dict[str, str] = {}
    airports_count: dict[str, int] = {}
    airlines_map: dict[str, str] = {}
    airlines_count: dict[str, int] = {}
    airlines_distance: dict[str, float] = {}
    aircraft_map: dict[str, str] = {}
    aircraft_count: dict[str, int] = {}
    aircraft_distance: dict[str, float] = {}
    routes_set: set[str] = set()
    routes_count: dict[str, int] = {}
    routes_distance: dict[str, float] = {}
    flights_per_year_obj: dict[int, int] = {}
    distance_per_year_obj: dict[int, float] = {}
    flights_per_month_obj: dict[int, int] = {}
    flights_per_weekday_obj: dict[int, int] = {}

    for f in flights:
        if f.arrival_airport.country == f.departure_airport.country:
            domestic_count += 1
        else:
            intl_count += 1

        total_distance += f.distance
        hrs, mins = f.duration.split(":")
        total_duration_minutes += int(hrs) * 60 + int(mins)

        fc = f.flight_class.value if f.flight_class else "Unknown"
        flight_classes_count[fc] = flight_classes_count.get(fc, 0) + 1

        reason = f.flight_reason.value if f.flight_reason else "Unknown"
        reasons_count[reason] = reasons_count.get(reason, 0) + 1

        seat = f.seat_type.value if f.seat_type else "Unknown"
        seat_type_count[seat] = seat_type_count.get(seat, 0) + 1

        from_continent = CONTINENTS_FOR_COUNTRIES.get(f.departure_airport.country, "Unknown")
        to_continent = CONTINENTS_FOR_COUNTRIES.get(f.arrival_airport.country, "Unknown")
        continents_count[from_continent] = continents_count.get(from_continent, 0) + 1
        continents_count[to_continent] = continents_count.get(to_continent, 0) + 1

        from_country = f.departure_airport.country
        to_country = f.arrival_airport.country
        countries_set.add(from_country)
        countries_set.add(to_country)
        countries_count[from_country] = countries_count.get(from_country, 0) + 1
        countries_count[to_country] = countries_count.get(to_country, 0) + 1

        from_iata = f.departure_airport.iata
        to_iata = f.arrival_airport.iata
        if from_iata not in airports_map:
            airports_map[from_iata] = f"{f.departure_airport.city}, {f.departure_airport.name}"
        if to_iata not in airports_map:
            airports_map[to_iata] = f"{f.arrival_airport.city}, {f.arrival_airport.name}"
        airports_count[from_iata] = airports_count.get(from_iata, 0) + 1
        airports_count[to_iata] = airports_count.get(to_iata, 0) + 1

        airline_iata = f.airline.iata
        if airline_iata not in airlines_map:
            airlines_map[airline_iata] = f.airline.name
        airlines_count[airline_iata] = airlines_count.get(airline_iata, 0) + 1
        airlines_distance[airline_iata] = airlines_distance.get(airline_iata, 0) + f.distance

        aircraft_icao = f.aircraft.icao
        if aircraft_icao not in aircraft_map:
            aircraft_map[aircraft_icao] = f.aircraft.name
        aircraft_count[aircraft_icao] = aircraft_count.get(aircraft_icao, 0) + 1
        aircraft_distance[aircraft_icao] = aircraft_distance.get(aircraft_icao, 0) + f.distance

        route = f"{f.departure_airport.iata}-{f.arrival_airport.iata}"
        routes_set.add(route)
        routes_count[route] = routes_count.get(route, 0) + 1
        routes_distance[route] = routes_distance.get(route, 0) + f.distance

        date = datetime.strptime(f.date, "%Y-%m-%d")
        year = date.year
        flights_per_year_obj[year] = flights_per_year_obj.get(year, 0) + 1
        distance_per_year_obj[year] = distance_per_year_obj.get(year, 0) + f.distance

        month = date.month - 1  # 0-indexed to match JS Date.getMonth()
        flights_per_month_obj[month] = flights_per_month_obj.get(month, 0) + 1

        weekday = date.isoweekday() % 7  # JS: 0=Sun,1=Mon..6=Sat; isoweekday: 1=Mon..7=Sun
        flights_per_weekday_obj[weekday] = flights_per_weekday_obj.get(weekday, 0) + 1

    def by_value(pair: tuple[str, int | float]) -> int | float:
        return -pair[1]

    flight_classes_by_count = sorted(flight_classes_count.items(), key=by_value)
    reasons_by_count = sorted(reasons_count.items(), key=by_value)
    seat_type_by_count = sorted(seat_type_count.items(), key=by_value)
    continents_by_count = sorted(continents_count.items(), key=by_value)
    countries_by_count = sorted(countries_count.items(), key=by_value)
    airports_by_count = sorted(airports_count.items(), key=by_value)
    airlines_by_count = sorted(airlines_count.items(), key=by_value)
    airlines_by_distance = sorted(airlines_distance.items(), key=by_value)
    aircraft_by_count = sorted(aircraft_count.items(), key=by_value)
    aircraft_by_distance = sorted(aircraft_distance.items(), key=by_value)
    routes_by_count = sorted(routes_count.items(), key=by_value)
    routes_by_distance = sorted(routes_distance.items(), key=by_value)

    # Build per-year series: use only the filtered years if provided, otherwise fill min→current
    if years_filter:
        for y_str in years_filter:
            y = int(y_str)
            flights_per_year_obj.setdefault(y, 0)
            distance_per_year_obj.setdefault(y, 0)
        flights_per_year = [(str(y), flights_per_year_obj.get(y, 0)) for y in sorted(int(y) for y in years_filter)]
        distance_per_year = [(str(y), distance_per_year_obj.get(y, 0.0)) for y in sorted(int(y) for y in years_filter)]
    else:
        start_year = min(flights_per_year_obj.keys())
        current_year = datetime.now().year
        for y in range(start_year, current_year + 1):
            flights_per_year_obj.setdefault(y, 0)
            distance_per_year_obj.setdefault(y, 0)
        flights_per_year = [(str(y), v) for y, v in sorted(flights_per_year_obj.items())]
        distance_per_year = [(str(y), v) for y, v in sorted(distance_per_year_obj.items())]
    years = [str(y) for y, _ in flights_per_year]

    # Fill all 12 months
    for m in range(12):
        flights_per_month_obj.setdefault(m, 0)
    flights_per_month = [(MONTH_NAMES[m], v) for m, v in sorted(flights_per_month_obj.items())]

    # Fill all 7 weekdays and shift Sunday to end (Monday first)
    for d in range(7):
        flights_per_weekday_obj.setdefault(d, 0)
    flights_per_weekday_list = [(DAY_NAMES[d], v) for d, v in sorted(flights_per_weekday_obj.items())]
    flights_per_weekday_list.append(flights_per_weekday_list.pop(0))  # move Sunday to end

    return FlightStats(
        total_count=len(flights),
        domestic_count=domestic_count,
        intl_count=intl_count,
        total_distance=total_distance,
        total_duration_minutes=total_duration_minutes,
        flight_classes_by_count=flight_classes_by_count,
        reasons_by_count=reasons_by_count,
        seat_type_by_count=seat_type_by_count,
        continents_by_count=continents_by_count,
        total_countries=len(countries_set),
        countries_by_count=countries_by_count,
        total_airports=len(airports_map),
        airports_by_count=airports_by_count,
        total_airlines=len(airlines_map),
        airlines_by_count=airlines_by_count,
        airlines_by_distance=airlines_by_distance,
        total_aircrafts=len(aircraft_map),
        aircraft_by_count=aircraft_by_count,
        aircraft_by_distance=aircraft_by_distance,
        total_routes=len(routes_set),
        routes_by_count=routes_by_count,
        routes_by_distance=routes_by_distance,
        flights_per_year=flights_per_year,
        distance_per_year=distance_per_year,
        flights_per_month=flights_per_month,
        flights_per_weekday=flights_per_weekday_list,
        airports_map=airports_map,
        airlines_map=airlines_map,
        aircraft_map=aircraft_map,
        years=years,
    )


def compute_visits_stats(visits: list[Visit]) -> VisitStats:
    if not visits:
        return VisitStats(cities_count=0, countries_count=0)

    cities: set[str] = set()
    countries: set[str] = set()
    for v in visits:
        cities.add(v.city)
        countries.add(v.country)

    return VisitStats(cities_count=len(cities), countries_count=len(countries))


def compute_flights_map(all_flights: list[Flight]) -> FlightMapData:
    flights = [f for f in all_flights if not f.is_planned]

    if not flights:
        return FlightMapData(routes=[], markers=[], center=(0.0, 0.0))

    route_map: dict[str, FlightMapRoute] = {}
    airport_set: set[str] = set()

    def create_key(from_iata: str, to_iata: str) -> str:
        key1 = f"{from_iata}%{to_iata}"
        key2 = f"{to_iata}%{from_iata}"
        return key1 if key1 < key2 else key2

    for flight in flights:
        key = create_key(flight.departure_airport.iata, flight.arrival_airport.iata)

        if key in route_map:
            route_map[key] = FlightMapRoute(
                a=route_map[key].a,
                b=route_map[key].b,
                count=route_map[key].count + 1,
            )
        else:
            route_map[key] = FlightMapRoute(
                a=(flight.departure_airport.lat, flight.departure_airport.lng),
                b=(flight.arrival_airport.lat, flight.arrival_airport.lng),
                count=1,
            )

        airport_set.add(f"{flight.departure_airport.lat}%{flight.departure_airport.lng}")
        airport_set.add(f"{flight.arrival_airport.lat}%{flight.arrival_airport.lng}")

    routes = list(route_map.values())

    markers: list[MapMarker] = []
    for coord_key in airport_set:
        lat_str, lng_str = coord_key.split("%")
        lat, lng = float(lat_str), float(lng_str)

        airport = next(
            (f.departure_airport for f in flights
             if f.departure_airport.lat == lat and f.departure_airport.lng == lng),
            None,
        ) or next(
            (f.arrival_airport for f in flights
             if f.arrival_airport.lat == lat and f.arrival_airport.lng == lng),
            None,
        )

        if airport:
            markers.append(MapMarker(pos=(lat, lng), popup=f"{airport.city} - {airport.name}"))

    center = _calculate_center([(float(k.split("%")[0]), float(k.split("%")[1])) for k in airport_set])

    return FlightMapData(routes=routes, markers=markers, center=center)


def _calculate_center(coordinates: list[tuple[float, float]]) -> tuple[float, float]:
    if not coordinates:
        return (0.0, 0.0)

    min_lat = min(c[0] for c in coordinates)
    max_lat = max(c[0] for c in coordinates)
    min_lng = min(c[1] for c in coordinates)
    max_lng = max(c[1] for c in coordinates)

    return ((min_lat + max_lat) / 2, (min_lng + max_lng) / 2)


def compute_visits_map(visits: list[Visit]) -> VisitMapData:
    if not visits:
        return VisitMapData(markers=[])

    markers = [MapMarker(pos=(v.lat, v.lng), popup=v.city) for v in visits]
    return VisitMapData(markers=markers)
