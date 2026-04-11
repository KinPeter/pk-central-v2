import pytest

from app.modules.flights.flights_types import (
    Aircraft,
    Airline,
    Airport,
    Flight,
    FlightClass,
    FlightReason,
    SeatType,
)
from app.modules.trips.trips_utils import (
    compute_flights_map,
    compute_flights_stats,
    compute_visits_map,
    compute_visits_stats,
)
from app.modules.visits.visits_types import Visit


# ── Shared fixtures ───────────────────────────────────────────────────────────

def make_airport(iata: str, city: str, country: str, lat: float, lng: float) -> Airport:
    return Airport(iata=iata, icao=iata + "X", name=f"{city} Airport", city=city, country=country, lat=lat, lng=lng)


def make_flight(
    id: str = "f1",
    date: str = "2024-03-15",
    dep_iata: str = "FRA",
    dep_city: str = "Frankfurt",
    dep_country: str = "Germany",
    dep_lat: float = 50.03,
    dep_lng: float = 8.56,
    arr_iata: str = "JFK",
    arr_city: str = "New York",
    arr_country: str = "USA",
    arr_lat: float = 40.64,
    arr_lng: float = -73.77,
    distance: float = 6200.0,
    duration: str = "08:30",
    airline_iata: str = "LH",
    airline_name: str = "Lufthansa",
    aircraft_icao: str = "A388",
    aircraft_name: str = "Airbus A380",
    flight_class: FlightClass = FlightClass.ECONOMY,
    flight_reason: FlightReason = FlightReason.LEISURE,
    seat_type: SeatType = SeatType.WINDOW,
    is_planned: bool = False,
) -> Flight:
    return Flight(
        id=id,
        flight_number="LH001",
        date=date,
        departure_airport=make_airport(dep_iata, dep_city, dep_country, dep_lat, dep_lng),
        arrival_airport=make_airport(arr_iata, arr_city, arr_country, arr_lat, arr_lng),
        departure_time="10:00",
        arrival_time="18:30",
        duration=duration,
        distance=distance,
        airline=Airline(iata=airline_iata, icao=airline_iata + "X", name=airline_name),
        aircraft=Aircraft(icao=aircraft_icao, name=aircraft_name),
        flight_class=flight_class,
        flight_reason=flight_reason,
        seat_type=seat_type,
        is_planned=is_planned,
    )


def make_visit(id: str, city: str, country: str, lat: float = 0.0, lng: float = 0.0, year: str | None = None) -> Visit:
    return Visit(id=id, city=city, country=country, lat=lat, lng=lng, year=year)


# ── compute_visits_stats ──────────────────────────────────────────────────────

class TestComputeVisitsStats:
    def test_empty_list_returns_zeros(self):
        result = compute_visits_stats([])
        assert result.cities_count == 0
        assert result.countries_count == 0

    def test_single_visit(self):
        result = compute_visits_stats([make_visit("v1", "Paris", "France")])
        assert result.cities_count == 1
        assert result.countries_count == 1

    def test_deduplicates_cities(self):
        visits = [
            make_visit("v1", "Paris", "France"),
            make_visit("v2", "Paris", "France"),
            make_visit("v3", "Lyon", "France"),
        ]
        result = compute_visits_stats(visits)
        assert result.cities_count == 2
        assert result.countries_count == 1

    def test_deduplicates_countries(self):
        visits = [
            make_visit("v1", "Paris", "France"),
            make_visit("v2", "Berlin", "Germany"),
            make_visit("v3", "Munich", "Germany"),
        ]
        result = compute_visits_stats(visits)
        assert result.cities_count == 3
        assert result.countries_count == 2

    def test_multiple_countries(self):
        visits = [make_visit(str(i), f"City{i}", f"Country{i}") for i in range(5)]
        result = compute_visits_stats(visits)
        assert result.cities_count == 5
        assert result.countries_count == 5


# ── compute_visits_map ────────────────────────────────────────────────────────

class TestComputeVisitsMap:
    def test_empty_list_returns_empty_markers(self):
        result = compute_visits_map([])
        assert result.markers == []

    def test_single_visit_produces_one_marker(self):
        visit = make_visit("v1", "Paris", "France", lat=48.85, lng=2.35)
        result = compute_visits_map([visit])
        assert len(result.markers) == 1
        assert result.markers[0].popup == "Paris"
        assert result.markers[0].pos == (48.85, 2.35)

    def test_multiple_visits_produce_multiple_markers(self):
        visits = [
            make_visit("v1", "Paris", "France", lat=48.85, lng=2.35),
            make_visit("v2", "Berlin", "Germany", lat=52.52, lng=13.40),
        ]
        result = compute_visits_map(visits)
        assert len(result.markers) == 2
        popups = {m.popup for m in result.markers}
        assert popups == {"Paris", "Berlin"}

    def test_marker_positions_are_correct(self):
        visit = make_visit("v1", "Tokyo", "Japan", lat=35.68, lng=139.69)
        result = compute_visits_map([visit])
        assert result.markers[0].pos == (35.68, 139.69)


# ── compute_flights_stats ─────────────────────────────────────────────────────

class TestComputeFlightsStats:
    def test_empty_list_returns_zeroed_stats(self):
        result = compute_flights_stats([])
        assert result.total_count == 0
        assert result.domestic_count == 0
        assert result.intl_count == 0
        assert result.total_distance == 0
        assert result.total_duration_minutes == 0
        assert result.total_countries == 0
        assert result.total_airports == 0
        assert result.total_airlines == 0
        assert result.total_aircrafts == 0
        assert result.total_routes == 0
        assert result.flight_classes_by_count == []
        assert result.flights_per_year == []
        assert len(result.flights_per_month) == 12
        assert len(result.flights_per_weekday) == 7
        assert result.years == []

    def test_planned_flights_excluded(self):
        flights = [
            make_flight(id="f1", is_planned=False),
            make_flight(id="f2", is_planned=True),
        ]
        result = compute_flights_stats(flights)
        assert result.total_count == 1

    def test_all_planned_treated_as_empty(self):
        result = compute_flights_stats([make_flight(is_planned=True)])
        assert result.total_count == 0

    def test_domestic_vs_international_count(self):
        flights = [
            make_flight(id="f1", dep_country="Germany", arr_country="Germany"),
            make_flight(id="f2", dep_country="Germany", arr_country="USA"),
        ]
        result = compute_flights_stats(flights)
        assert result.domestic_count == 1
        assert result.intl_count == 1

    def test_total_distance_and_duration(self):
        flights = [
            make_flight(id="f1", distance=1000.0, duration="02:00"),
            make_flight(id="f2", distance=500.0, duration="01:30"),
        ]
        result = compute_flights_stats(flights)
        assert result.total_distance == 1500.0
        assert result.total_duration_minutes == 210

    def test_flight_classes_counted(self):
        flights = [
            make_flight(id="f1", flight_class=FlightClass.ECONOMY),
            make_flight(id="f2", flight_class=FlightClass.ECONOMY),
            make_flight(id="f3", flight_class=FlightClass.BUSINESS),
        ]
        result = compute_flights_stats(flights)
        classes = dict(result.flight_classes_by_count)
        assert classes["Economy"] == 2
        assert classes["Business"] == 1

    def test_flight_classes_sorted_by_count_descending(self):
        flights = [
            make_flight(id="f1", flight_class=FlightClass.BUSINESS),
            make_flight(id="f2", flight_class=FlightClass.ECONOMY),
            make_flight(id="f3", flight_class=FlightClass.ECONOMY),
        ]
        result = compute_flights_stats(flights)
        assert result.flight_classes_by_count[0][0] == "Economy"

    def test_reasons_counted(self):
        flights = [
            make_flight(id="f1", flight_reason=FlightReason.LEISURE),
            make_flight(id="f2", flight_reason=FlightReason.BUSINESS),
        ]
        result = compute_flights_stats(flights)
        reasons = dict(result.reasons_by_count)
        assert reasons["Leisure"] == 1
        assert reasons["Business"] == 1

    def test_seat_types_counted(self):
        flights = [
            make_flight(id="f1", seat_type=SeatType.WINDOW),
            make_flight(id="f2", seat_type=SeatType.WINDOW),
            make_flight(id="f3", seat_type=SeatType.AISLE),
        ]
        result = compute_flights_stats(flights)
        seats = dict(result.seat_type_by_count)
        assert seats["Window"] == 2
        assert seats["Aisle"] == 1

    def test_continents_counted(self):
        flights = [make_flight(id="f1", dep_country="Germany", arr_country="USA")]
        result = compute_flights_stats(flights)
        continents = dict(result.continents_by_count)
        assert continents.get("Europe", 0) == 1
        assert continents.get("North America", 0) == 1

    def test_unknown_country_uses_unknown_continent(self):
        flights = [make_flight(id="f1", dep_country="Narnia", arr_country="Germany")]
        result = compute_flights_stats(flights)
        continents = dict(result.continents_by_count)
        assert continents.get("Unknown", 0) == 1

    def test_countries_deduplication(self):
        flights = [
            make_flight(id="f1", dep_country="Germany", arr_country="France"),
            make_flight(id="f2", dep_country="Germany", arr_country="Spain"),
        ]
        result = compute_flights_stats(flights)
        assert result.total_countries == 3  # Germany, France, Spain

    def test_airports_map_and_count(self):
        flights = [make_flight(id="f1", dep_iata="FRA", dep_city="Frankfurt", arr_iata="JFK", arr_city="New York")]
        result = compute_flights_stats(flights)
        assert result.total_airports == 2
        assert "FRA" in result.airports_map
        assert "JFK" in result.airports_map
        assert result.airports_map["FRA"] == "Frankfurt, Frankfurt Airport"

    def test_same_airport_used_multiple_times(self):
        flights = [
            make_flight(id="f1", dep_iata="FRA", arr_iata="JFK"),
            make_flight(id="f2", dep_iata="FRA", arr_iata="CDG",
                        arr_city="Paris", arr_country="France", arr_lat=49.01, arr_lng=2.55),
        ]
        result = compute_flights_stats(flights)
        assert result.total_airports == 3
        airports = dict(result.airports_by_count)
        assert airports["FRA"] == 2

    def test_airlines_map_and_count(self):
        flights = [
            make_flight(id="f1", airline_iata="LH", airline_name="Lufthansa", distance=1000.0),
            make_flight(id="f2", airline_iata="LH", airline_name="Lufthansa", distance=500.0),
            make_flight(id="f3", airline_iata="BA", airline_name="British Airways", distance=200.0),
        ]
        result = compute_flights_stats(flights)
        assert result.total_airlines == 2
        by_count = dict(result.airlines_by_count)
        assert by_count["LH"] == 2
        assert by_count["BA"] == 1
        by_distance = dict(result.airlines_by_distance)
        assert by_distance["LH"] == 1500.0

    def test_aircraft_map_and_count(self):
        flights = [
            make_flight(id="f1", aircraft_icao="B738", aircraft_name="Boeing 737"),
            make_flight(id="f2", aircraft_icao="B738", aircraft_name="Boeing 737", distance=300.0),
        ]
        result = compute_flights_stats(flights)
        assert result.total_aircrafts == 1
        assert "B738" in result.aircraft_map
        by_count = dict(result.aircraft_by_count)
        assert by_count["B738"] == 2

    def test_routes_are_directional_in_stats(self):
        # FRA→JFK and JFK→FRA are treated as two separate routes in stats
        # (unlike compute_flights_map which merges reverse routes)
        flights = [
            make_flight(id="f1", dep_iata="FRA", arr_iata="JFK"),
            make_flight(id="f2", dep_iata="JFK", dep_lat=40.64, dep_lng=-73.77,
                        arr_iata="FRA", arr_lat=50.03, arr_lng=8.56,
                        dep_country="USA", arr_country="Germany"),
        ]
        result = compute_flights_stats(flights)
        assert result.total_routes == 2
        route_keys = {r for r, _ in result.routes_by_count}
        assert "FRA-JFK" in route_keys
        assert "JFK-FRA" in route_keys

    def test_routes_counted_by_direction_pair(self):
        flights = [
            make_flight(id="f1", dep_iata="FRA", arr_iata="JFK"),
            make_flight(id="f2", dep_iata="FRA", arr_iata="JFK"),
        ]
        result = compute_flights_stats(flights)
        routes = dict(result.routes_by_count)
        assert routes["FRA-JFK"] == 2

    def test_flights_per_month_all_twelve_present(self):
        result = compute_flights_stats([make_flight(date="2024-06-01")])
        assert len(result.flights_per_month) == 12
        months = dict(result.flights_per_month)
        assert months["June"] == 1
        assert months["January"] == 0

    def test_flights_per_weekday_monday_first(self):
        result = compute_flights_stats([make_flight(date="2024-01-01")])  # Monday
        assert len(result.flights_per_weekday) == 7
        assert result.flights_per_weekday[0][0] == "Monday"
        assert result.flights_per_weekday[-1][0] == "Sunday"

    def test_flights_per_weekday_sunday_at_end(self):
        # 2024-01-07 is a Sunday
        result = compute_flights_stats([make_flight(date="2024-01-07")])
        weekdays = dict(result.flights_per_weekday)
        assert weekdays["Sunday"] == 1
        assert result.flights_per_weekday[-1][0] == "Sunday"

    def test_flights_per_year_fills_gaps_without_filter(self):
        flights = [
            make_flight(id="f1", date="2022-01-01"),
            make_flight(id="f2", date="2024-01-01"),
        ]
        result = compute_flights_stats(flights)
        years_in_result = [y for y, _ in result.flights_per_year]
        # 2023 gap should be filled
        assert "2023" in years_in_result

    def test_years_filter_restricts_per_year_output(self):
        flights = [
            make_flight(id="f1", date="2022-01-01"),
            make_flight(id="f2", date="2023-01-01"),
            make_flight(id="f3", date="2024-01-01"),
        ]
        result = compute_flights_stats(flights, years_filter=["2022", "2023"])
        years_in_result = [y for y, _ in result.flights_per_year]
        assert years_in_result == ["2022", "2023"]
        assert "2024" not in years_in_result

    def test_years_filter_pads_missing_years_with_zero(self):
        flights = [make_flight(id="f1", date="2022-01-01")]
        result = compute_flights_stats(flights, years_filter=["2022", "2023"])
        per_year = dict(result.flights_per_year)
        assert per_year["2022"] == 1
        assert per_year["2023"] == 0

    def test_years_filter_sorted_ascending(self):
        flights = [
            make_flight(id="f1", date="2024-01-01"),
            make_flight(id="f2", date="2022-01-01"),
        ]
        result = compute_flights_stats(flights, years_filter=["2024", "2022"])
        years_in_result = [y for y, _ in result.flights_per_year]
        assert years_in_result == ["2022", "2024"]

    def test_years_helper_field_matches_flights_per_year(self):
        flights = [make_flight(id="f1", date="2024-03-15")]
        result = compute_flights_stats(flights)
        assert result.years == [y for y, _ in result.flights_per_year]

    def test_none_flight_class_uses_unknown(self):
        f = make_flight(id="f1")
        f.flight_class = None
        result = compute_flights_stats([f])
        classes = dict(result.flight_classes_by_count)
        assert classes.get("Unknown", 0) == 1

    def test_none_flight_reason_uses_unknown(self):
        f = make_flight(id="f1")
        f.flight_reason = None
        result = compute_flights_stats([f])
        reasons = dict(result.reasons_by_count)
        assert reasons.get("Unknown", 0) == 1

    def test_none_seat_type_uses_unknown(self):
        f = make_flight(id="f1")
        f.seat_type = None
        result = compute_flights_stats([f])
        seats = dict(result.seat_type_by_count)
        assert seats.get("Unknown", 0) == 1


# ── compute_flights_map ───────────────────────────────────────────────────────

class TestComputeFlightsMap:
    def test_empty_list_returns_empty(self):
        result = compute_flights_map([])
        assert result.routes == []
        assert result.markers == []
        assert result.center == (0.0, 0.0)

    def test_planned_flights_excluded(self):
        result = compute_flights_map([make_flight(is_planned=True)])
        assert result.routes == []
        assert result.markers == []

    def test_single_flight_produces_one_route_two_markers(self):
        result = compute_flights_map([make_flight()])
        assert len(result.routes) == 1
        assert len(result.markers) == 2

    def test_route_coordinates_correct(self):
        f = make_flight(dep_lat=50.03, dep_lng=8.56, arr_lat=40.64, arr_lng=-73.77)
        result = compute_flights_map([f])
        route = result.routes[0]
        coords = {route.a, route.b}
        assert (50.03, 8.56) in coords
        assert (40.64, -73.77) in coords

    def test_route_count_is_one_for_single_flight(self):
        result = compute_flights_map([make_flight()])
        assert result.routes[0].count == 1

    def test_repeated_route_increments_count(self):
        flights = [make_flight(id="f1"), make_flight(id="f2")]
        result = compute_flights_map(flights)
        assert len(result.routes) == 1
        assert result.routes[0].count == 2

    def test_reverse_route_merges_with_forward(self):
        f1 = make_flight(id="f1", dep_iata="FRA", dep_lat=50.03, dep_lng=8.56,
                          arr_iata="JFK", arr_lat=40.64, arr_lng=-73.77)
        f2 = make_flight(id="f2", dep_iata="JFK", dep_lat=40.64, dep_lng=-73.77,
                          dep_country="USA",
                          arr_iata="FRA", arr_lat=50.03, arr_lng=8.56,
                          arr_country="Germany")
        result = compute_flights_map([f1, f2])
        assert len(result.routes) == 1
        assert result.routes[0].count == 2

    def test_two_different_routes_produce_two_entries(self):
        f1 = make_flight(id="f1", dep_iata="FRA", arr_iata="JFK")
        f2 = make_flight(id="f2", dep_iata="FRA", dep_lat=50.03, dep_lng=8.56,
                          arr_iata="CDG", arr_lat=49.01, arr_lng=2.55,
                          arr_city="Paris", arr_country="France")
        result = compute_flights_map([f1, f2])
        assert len(result.routes) == 2

    def test_airport_deduplication_in_markers(self):
        # Two flights from same departure airport — should only produce one marker for it
        f1 = make_flight(id="f1", dep_iata="FRA", dep_lat=50.03, dep_lng=8.56, arr_iata="JFK", arr_lat=40.64, arr_lng=-73.77)
        f2 = make_flight(id="f2", dep_iata="FRA", dep_lat=50.03, dep_lng=8.56,
                          arr_iata="CDG", arr_lat=49.01, arr_lng=2.55,
                          arr_city="Paris", arr_country="France")
        result = compute_flights_map([f1, f2])
        assert len(result.markers) == 3  # FRA, JFK, CDG

    def test_marker_popup_format(self):
        f = make_flight(dep_iata="FRA", dep_city="Frankfurt", arr_iata="JFK", arr_city="New York")
        result = compute_flights_map([f])
        popups = {m.popup for m in result.markers}
        assert "Frankfurt - Frankfurt Airport" in popups
        assert "New York - New York Airport" in popups

    def test_center_is_midpoint_of_bounding_box(self):
        f = make_flight(dep_lat=0.0, dep_lng=0.0, arr_lat=10.0, arr_lng=20.0)
        result = compute_flights_map([f])
        assert result.center == (5.0, 10.0)

    def test_center_single_point(self):
        # When dep and arr are at the same lat/lng (edge case)
        f = make_flight(dep_lat=10.0, dep_lng=20.0, arr_lat=10.0, arr_lng=20.0,
                        dep_iata="AAA", arr_iata="BBB")
        result = compute_flights_map([f])
        assert result.center == (10.0, 20.0)
