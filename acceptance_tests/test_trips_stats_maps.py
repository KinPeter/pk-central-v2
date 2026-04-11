import pytest


FLIGHT_FRA_JFK = {
    "flightNumber": "LH001",
    "date": "2024-03-15",
    "departureAirport": {
        "iata": "FRA",
        "icao": "EDDF",
        "name": "Frankfurt Airport",
        "city": "Frankfurt",
        "country": "Germany",
        "lat": 50.0379,
        "lng": 8.5622,
    },
    "arrivalAirport": {
        "iata": "JFK",
        "icao": "KJFK",
        "name": "John F. Kennedy International Airport",
        "city": "New York",
        "country": "USA",
        "lat": 40.6413,
        "lng": -73.7781,
    },
    "departureTime": "10:00",
    "arrivalTime": "13:00",
    "duration": "08:00",
    "distance": 6200.0,
    "airline": {"iata": "LH", "icao": "DLH", "name": "Lufthansa"},
    "aircraft": {"icao": "A388", "name": "Airbus A380"},
    "flightClass": "Economy",
    "flightReason": "Leisure",
    "seatType": "Window",
    "isPlanned": False,
}

FLIGHT_LHR_CDG_2023 = {
    "flightNumber": "BA456",
    "date": "2023-06-10",
    "departureAirport": {
        "iata": "LHR",
        "icao": "EGLL",
        "name": "Heathrow Airport",
        "city": "London",
        "country": "UK",
        "lat": 51.4700,
        "lng": -0.4543,
    },
    "arrivalAirport": {
        "iata": "CDG",
        "icao": "LFPG",
        "name": "Charles de Gaulle Airport",
        "city": "Paris",
        "country": "France",
        "lat": 49.0097,
        "lng": 2.5479,
    },
    "departureTime": "09:00",
    "arrivalTime": "11:20",
    "duration": "01:20",
    "distance": 344.0,
    "airline": {"iata": "BA", "icao": "BAW", "name": "British Airways"},
    "aircraft": {"icao": "A320", "name": "Airbus A320"},
    "flightClass": "Business",
    "flightReason": "Business",
    "seatType": "Aisle",
    "isPlanned": False,
}

FLIGHT_PLANNED = {
    "flightNumber": "LH999",
    "date": "2025-12-01",
    "departureAirport": FLIGHT_FRA_JFK["departureAirport"],
    "arrivalAirport": FLIGHT_FRA_JFK["arrivalAirport"],
    "departureTime": "10:00",
    "arrivalTime": "18:00",
    "duration": "08:00",
    "distance": 6200.0,
    "airline": {"iata": "LH", "icao": "DLH", "name": "Lufthansa"},
    "aircraft": {"icao": "A388", "name": "Airbus A380"},
    "isPlanned": True,
}

VISIT_PARIS_2023 = {"city": "Paris", "country": "France", "lat": 48.8566, "lng": 2.3522, "year": "2023"}
VISIT_BERLIN_2024 = {"city": "Berlin", "country": "Germany", "lat": 52.5200, "lng": 13.4050, "year": "2024"}
VISIT_TOKYO_NO_YEAR = {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lng": 139.6503}


def create_flight(client, token, data):
    r = client.post("/flights/", headers={"Authorization": f"Bearer {token}"}, json=data)
    assert r.status_code == 201
    return r.json()


def create_visit(client, token, data):
    r = client.post("/visits/", headers={"Authorization": f"Bearer {token}"}, json=data)
    assert r.status_code == 201
    return r.json()


# ── POST /trips/stats (auth-protected) ───────────────────────────────────────

class TestTripsStatsAuth:
    def test_no_filters_returns_all_completed_flights_and_visits(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)
        create_flight(client, token, FLIGHT_LHR_CDG_2023)
        create_flight(client, token, FLIGHT_PLANNED)  # should be excluded
        create_visit(client, token, VISIT_PARIS_2023)
        create_visit(client, token, VISIT_BERLIN_2024)

        response = client.post(
            "/trips/stats",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        data = response.json()

        flights = data["flights"]
        assert flights["totalCount"] == 2  # planned excluded
        assert flights["totalDistance"] == FLIGHT_FRA_JFK["distance"] + FLIGHT_LHR_CDG_2023["distance"]
        assert flights["totalAirlines"] == 2
        assert flights["totalAirports"] == 4
        assert flights["totalRoutes"] == 2
        assert len(flights["flightsPerMonth"]) == 12
        assert len(flights["flightsPerWeekday"]) == 7
        assert flights["flightsPerWeekday"][0][0] == "Monday"
        assert flights["flightsPerWeekday"][-1][0] == "Sunday"
        assert len(flights["years"]) > 0

        visits = data["visits"]
        assert visits["citiesCount"] == 2
        assert visits["countriesCount"] == 2

    def test_year_filter_returns_only_matching_year(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)       # 2024
        create_flight(client, token, FLIGHT_LHR_CDG_2023)  # 2023
        create_visit(client, token, VISIT_PARIS_2023)       # 2023
        create_visit(client, token, VISIT_BERLIN_2024)      # 2024

        response = client.post(
            "/trips/stats",
            headers={"Authorization": f"Bearer {token}"},
            json={"year": ["2024"]},
        )
        assert response.status_code == 200
        data = response.json()

        flights = data["flights"]
        assert flights["totalCount"] == 1
        assert flights["flightsPerYear"] == [["2024", 1]]
        assert flights["years"] == ["2024"]

        visits = data["visits"]
        assert visits["citiesCount"] == 1
        assert visits["countriesCount"] == 1

    def test_planned_flights_excluded_from_stats(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_PLANNED)

        response = client.post(
            "/trips/stats",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["flights"]["totalCount"] == 0

    def test_empty_data_returns_zeroed_stats(self, client, login_user):
        token, user_id, _ = login_user

        response = client.post(
            "/trips/stats",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["flights"]["totalCount"] == 0
        assert data["visits"]["citiesCount"] == 0
        assert data["visits"]["countriesCount"] == 0

    def test_invalid_token_returns_401(self, client):
        response = client.post(
            "/trips/stats",
            headers={"Authorization": "Bearer invalid_token"},
            json={},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_no_auth_returns_401(self, client):
        response = client.post("/trips/stats", json={})
        assert response.status_code == 401

    def test_invalid_year_format_returns_422(self, client, login_user):
        token, _, _ = login_user
        response = client.post(
            "/trips/stats",
            headers={"Authorization": f"Bearer {token}"},
            json={"year": ["24"]},  # must be 4 digits
        )
        assert response.status_code == 422


# ── POST /trips/maps (auth-protected) ────────────────────────────────────────

class TestTripsMapsAuth:
    def test_no_filters_returns_all_completed_flights_and_visits(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)
        create_flight(client, token, FLIGHT_LHR_CDG_2023)
        create_flight(client, token, FLIGHT_PLANNED)  # should be excluded
        create_visit(client, token, VISIT_PARIS_2023)
        create_visit(client, token, VISIT_TOKYO_NO_YEAR)

        response = client.post(
            "/trips/maps",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        data = response.json()

        flights = data["flights"]
        assert len(flights["routes"]) == 2  # 2 distinct routes, planned excluded
        assert len(flights["markers"]) == 4  # FRA, JFK, LHR, CDG
        assert len(flights["center"]) == 2

        visits = data["visits"]
        assert len(visits["markers"]) == 2
        popups = {m["popup"] for m in visits["markers"]}
        assert "Paris" in popups
        assert "Tokyo" in popups

    def test_year_filter_restricts_flights_and_visits(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)       # 2024
        create_flight(client, token, FLIGHT_LHR_CDG_2023)  # 2023
        create_visit(client, token, VISIT_PARIS_2023)
        create_visit(client, token, VISIT_BERLIN_2024)

        response = client.post(
            "/trips/maps",
            headers={"Authorization": f"Bearer {token}"},
            json={"year": ["2023"]},
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["flights"]["routes"]) == 1
        assert len(data["flights"]["markers"]) == 2  # LHR, CDG
        assert len(data["visits"]["markers"]) == 1
        assert data["visits"]["markers"][0]["popup"] == "Paris"

    def test_planned_flights_excluded_from_map(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_PLANNED)

        response = client.post(
            "/trips/maps",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["flights"]["routes"] == []
        assert data["flights"]["markers"] == []
        assert data["flights"]["center"] == [0.0, 0.0]

    def test_invalid_token_returns_401(self, client):
        response = client.post(
            "/trips/maps",
            headers={"Authorization": "Bearer invalid_token"},
            json={},
        )
        assert response.status_code == 401

    def test_no_auth_returns_401(self, client):
        response = client.post("/trips/maps", json={})
        assert response.status_code == 401

    def test_invalid_year_format_returns_422(self, client, login_user):
        token, _, _ = login_user
        response = client.post(
            "/trips/maps",
            headers={"Authorization": f"Bearer {token}"},
            json={"year": ["2024-01"]},
        )
        assert response.status_code == 422


# ── POST /trips/{user_id}/stats (public) ─────────────────────────────────────

class TestUserTripsStatsPublic:
    def test_no_filters_returns_all_completed_flights_and_visits(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)
        create_flight(client, token, FLIGHT_LHR_CDG_2023)
        create_visit(client, token, VISIT_PARIS_2023)
        create_visit(client, token, VISIT_BERLIN_2024)

        response = client.post(f"/trips/{user_id}/stats", json={})
        assert response.status_code == 200
        data = response.json()

        assert data["flights"]["totalCount"] == 2
        assert data["visits"]["citiesCount"] == 2
        assert data["visits"]["countriesCount"] == 2

    def test_year_filter_returns_only_matching_year(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)       # 2024
        create_flight(client, token, FLIGHT_LHR_CDG_2023)  # 2023
        create_visit(client, token, VISIT_PARIS_2023)
        create_visit(client, token, VISIT_BERLIN_2024)

        response = client.post(f"/trips/{user_id}/stats", json={"year": ["2023"]})
        assert response.status_code == 200
        data = response.json()

        assert data["flights"]["totalCount"] == 1
        assert data["visits"]["citiesCount"] == 1

    def test_unknown_user_id_returns_empty_stats(self, client):
        response = client.post("/trips/nonexistent-user-id/stats", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["flights"]["totalCount"] == 0
        assert data["visits"]["citiesCount"] == 0

    def test_no_auth_required(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)

        # No Authorization header
        response = client.post(f"/trips/{user_id}/stats", json={})
        assert response.status_code == 200

    def test_invalid_year_format_returns_422(self, client, login_user):
        _, user_id, _ = login_user
        response = client.post(f"/trips/{user_id}/stats", json={"year": ["24"]})
        assert response.status_code == 422


# ── POST /trips/{user_id}/maps (public) ──────────────────────────────────────

class TestUserTripsMapsPublic:
    def test_no_filters_returns_all_completed_flights_and_visits(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)
        create_visit(client, token, VISIT_PARIS_2023)

        response = client.post(f"/trips/{user_id}/maps", json={})
        assert response.status_code == 200
        data = response.json()

        assert len(data["flights"]["routes"]) == 1
        assert len(data["flights"]["markers"]) == 2
        assert len(data["visits"]["markers"]) == 1
        assert data["visits"]["markers"][0]["popup"] == "Paris"

    def test_year_filter_restricts_map_data(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)       # 2024
        create_flight(client, token, FLIGHT_LHR_CDG_2023)  # 2023
        create_visit(client, token, VISIT_PARIS_2023)
        create_visit(client, token, VISIT_BERLIN_2024)

        response = client.post(f"/trips/{user_id}/maps", json={"year": ["2024"]})
        assert response.status_code == 200
        data = response.json()

        assert len(data["flights"]["routes"]) == 1
        assert len(data["visits"]["markers"]) == 1
        assert data["visits"]["markers"][0]["popup"] == "Berlin"

    def test_unknown_user_id_returns_empty_map(self, client):
        response = client.post("/trips/nonexistent-user-id/maps", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["flights"]["routes"] == []
        assert data["flights"]["markers"] == []
        assert data["visits"]["markers"] == []

    def test_no_auth_required(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)

        response = client.post(f"/trips/{user_id}/maps", json={})
        assert response.status_code == 200

    def test_invalid_year_format_returns_422(self, client, login_user):
        _, user_id, _ = login_user
        response = client.post(f"/trips/{user_id}/maps", json={"year": ["2024-01"]})
        assert response.status_code == 422


# ── GET /trips/{user_id} (public, with optional year filter) ─────────────────

class TestGetUserTrips:
    def test_no_filter_returns_all_flights_and_visits(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)
        create_flight(client, token, FLIGHT_LHR_CDG_2023)
        create_visit(client, token, VISIT_PARIS_2023)
        create_visit(client, token, VISIT_BERLIN_2024)

        response = client.get(f"/trips/{user_id}")
        assert response.status_code == 200
        data = response.json()

        assert len(data["flights"]) == 2
        assert len(data["visits"]) == 2

    def test_year_filter_returns_only_matching_flights_and_visits(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)        # 2024
        create_flight(client, token, FLIGHT_LHR_CDG_2023)  # 2023
        create_visit(client, token, VISIT_PARIS_2023)       # 2023
        create_visit(client, token, VISIT_BERLIN_2024)      # 2024

        response = client.get(f"/trips/{user_id}?year=2024")
        assert response.status_code == 200
        data = response.json()

        assert len(data["flights"]) == 1
        assert data["flights"][0]["date"] == FLIGHT_FRA_JFK["date"]
        assert len(data["visits"]) == 1
        assert data["visits"][0]["city"] == "Berlin"

    def test_multi_year_filter_returns_matching_flights_and_visits(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)        # 2024
        create_flight(client, token, FLIGHT_LHR_CDG_2023)  # 2023
        create_visit(client, token, VISIT_PARIS_2023)       # 2023
        create_visit(client, token, VISIT_BERLIN_2024)      # 2024
        create_visit(client, token, VISIT_TOKYO_NO_YEAR)    # no year → excluded

        response = client.get(f"/trips/{user_id}?year=2024&year=2023")
        assert response.status_code == 200
        data = response.json()

        assert len(data["flights"]) == 2
        assert len(data["visits"]) == 2

    def test_unknown_user_returns_empty(self, client):
        response = client.get("/trips/nonexistent-user-id")
        assert response.status_code == 200
        data = response.json()
        assert data["flights"] == []
        assert data["visits"] == []

    def test_no_auth_required(self, client, login_user):
        token, user_id, _ = login_user
        create_flight(client, token, FLIGHT_FRA_JFK)

        response = client.get(f"/trips/{user_id}")
        assert response.status_code == 200

    def test_invalid_year_format_returns_422(self, client, login_user):
        _, user_id, _ = login_user
        response = client.get(f"/trips/{user_id}?year=24")
        assert response.status_code == 422
