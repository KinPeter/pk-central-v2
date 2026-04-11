import pytest


class TestCreateAndGetFlights:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a flight
        flight_data = {
            "flightNumber": "LH123",
            "date": "2024-01-01",
            "departureAirport": {
                "iata": "FRA",
                "icao": "EDDF",
                "name": "Frankfurt",
                "city": "Frankfurt",
                "country": "Germany",
                "lat": 50.0379,
                "lng": 8.5622,
            },
            "arrivalAirport": {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "JFK",
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
            "registration": "D-AIMA",
            "seatNumber": "12A",
            "seatType": "Window",
            "flightClass": "Business",
            "flightReason": "Business",
            "note": "Work trip",
            "isPlanned": True,
        }
        response = client.post(
            "/flights/",
            headers={"Authorization": f"Bearer {token}"},
            json=flight_data,
        )
        assert response.status_code == 201
        created_flight = response.json()
        assert "id" in created_flight
        for k, v in flight_data.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    assert created_flight[k][subk] == subv
            else:
                assert (
                    created_flight[k] == v
                    or created_flight[k] == v.upper()
                    or created_flight[k] == v.capitalize()
                )

        # Create another flight (minimal required fields)
        flight_data2 = {
            "flightNumber": "BA456",
            "date": "2024-02-02",
            "departureAirport": {
                "iata": "LHR",
                "icao": "EGLL",
                "name": "Heathrow",
                "city": "London",
                "country": "UK",
                "lat": 51.4700,
                "lng": -0.4543,
            },
            "arrivalAirport": {
                "iata": "CDG",
                "icao": "LFPG",
                "name": "Charles de Gaulle",
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
        }
        response = client.post(
            "/flights/",
            headers={"Authorization": f"Bearer {token}"},
            json=flight_data2,
        )
        assert response.status_code == 201
        created_flight2 = response.json()
        assert "id" in created_flight2
        for k, v in flight_data2.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    assert created_flight2[k][subk] == subv
            else:
                assert (
                    created_flight2[k] == v
                    or created_flight2[k] == v.upper()
                    or created_flight2[k] == v.capitalize()
                )

        # Get all flights
        response = client.get(
            "/flights/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        entities = data["entities"]
        assert len(entities) >= 2
        # Check that at least the two created flights are present
        found1 = any(e["flightNumber"] == flight_data["flightNumber"] for e in entities)
        found2 = any(
            e["flightNumber"] == flight_data2["flightNumber"] for e in entities
        )
        assert found1 and found2

    def test_get_planned_flights(self, client, login_user):
        token, user_id, email = login_user

        # Create 2 planned flights (future date, isPlanned: true)
        planned1 = {
            "flightNumber": "PLN001",
            "date": "2099-01-01",
            "departureAirport": {
                "iata": "FRA",
                "icao": "EDDF",
                "name": "Frankfurt",
                "city": "Frankfurt",
                "country": "Germany",
                "lat": 50.0379,
                "lng": 8.5622,
            },
            "arrivalAirport": {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "JFK",
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
            "isPlanned": True,
        }
        planned2 = {
            "flightNumber": "PLN002",
            "date": "2099-02-02",
            "departureAirport": {
                "iata": "LHR",
                "icao": "EGLL",
                "name": "Heathrow",
                "city": "London",
                "country": "UK",
                "lat": 51.4700,
                "lng": -0.4543,
            },
            "arrivalAirport": {
                "iata": "CDG",
                "icao": "LFPG",
                "name": "Charles de Gaulle",
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
            "isPlanned": True,
        }
        # Create 1 non-planned flight
        not_planned = {
            "flightNumber": "NPL001",
            "date": "2020-01-01",
            "departureAirport": {
                "iata": "FRA",
                "icao": "EDDF",
                "name": "Frankfurt",
                "city": "Frankfurt",
                "country": "Germany",
                "lat": 50.0379,
                "lng": 8.5622,
            },
            "arrivalAirport": {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "JFK",
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
            "isPlanned": False,
        }

        for data in [planned1, planned2, not_planned]:
            response = client.post(
                "/flights/",
                headers={"Authorization": f"Bearer {token}"},
                json=data,
            )
            assert response.status_code == 201

        # Get only planned flights
        response = client.get(
            "/flights/?is_planned=true",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        entities = data["entities"]
        assert len(entities) == 2
        numbers = {e["flightNumber"] for e in entities}
        assert numbers == {"PLN001", "PLN002"}

    def test_create_invalid_token(self, client, login_user):
        response = client.post(
            "/flights/",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "flightNumber": "LH123",
                "date": "2024-01-01",
                "departure_airport": {
                    "iata": "FRA",
                    "icao": "EDDF",
                    "name": "Frankfurt",
                    "city": "Frankfurt",
                    "country": "Germany",
                    "lat": 50.0379,
                    "lng": 8.5622,
                },
                "arrival_airport": {
                    "iata": "JFK",
                    "icao": "KJFK",
                    "name": "JFK",
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
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_get_flights_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        flight_data = {
            "flightNumber": "LH123",
            "date": "2024-01-01",
            "departure_airport": {
                "iata": "FRA",
                "icao": "EDDF",
                "name": "Frankfurt",
                "city": "Frankfurt",
                "country": "Germany",
                "lat": 50.0379,
                "lng": 8.5622,
            },
            "arrival_airport": {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "JFK",
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
        }
        response = client.post(
            "/flights/",
            headers={"Authorization": f"Bearer {token}"},
            json=flight_data,
        )
        assert response.status_code == 201
        # Get with invalid token
        response = client.get(
            "/flights/",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "flight_data,expected_msg",
        [
            # Invalid date
            (
                {
                    "flightNumber": "LH123",
                    "date": "not-a-date",
                    "departureAirport": {
                        "iata": "FRA",
                        "icao": "EDDF",
                        "name": "Frankfurt",
                        "city": "Frankfurt",
                        "country": "Germany",
                        "lat": 50.0379,
                        "lng": 8.5622,
                    },
                    "arrivalAirport": {
                        "iata": "JFK",
                        "icao": "KJFK",
                        "name": "JFK",
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
                },
                "String should match pattern",
            ),
            # Flight number too short
            (
                {
                    "flightNumber": "LH",
                    "date": "2024-01-01",
                    "departureAirport": {
                        "iata": "FRA",
                        "icao": "EDDF",
                        "name": "Frankfurt",
                        "city": "Frankfurt",
                        "country": "Germany",
                        "lat": 50.0379,
                        "lng": 8.5622,
                    },
                    "arrivalAirport": {
                        "iata": "JFK",
                        "icao": "KJFK",
                        "name": "JFK",
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
                },
                "at least 3 characters",
            ),
            # Distance negative
            (
                {
                    "flightNumber": "LH123",
                    "date": "2024-01-01",
                    "departureAirport": {
                        "iata": "FRA",
                        "icao": "EDDF",
                        "name": "Frankfurt",
                        "city": "Frankfurt",
                        "country": "Germany",
                        "lat": 50.0379,
                        "lng": 8.5622,
                    },
                    "arrivalAirport": {
                        "iata": "JFK",
                        "icao": "KJFK",
                        "name": "JFK",
                        "city": "New York",
                        "country": "USA",
                        "lat": 40.6413,
                        "lng": -73.7781,
                    },
                    "departureTime": "10:00",
                    "arrivalTime": "13:00",
                    "duration": "08:00",
                    "distance": -100.0,
                    "airline": {"iata": "LH", "icao": "DLH", "name": "Lufthansa"},
                    "aircraft": {"icao": "A388", "name": "Airbus A380"},
                },
                "greater than 0",
            ),
            # Missing required fields
            (
                {
                    "date": "2024-01-01",
                    "departureAirport": {
                        "iata": "FRA",
                        "icao": "EDDF",
                        "name": "Frankfurt",
                        "city": "Frankfurt",
                        "country": "Germany",
                        "lat": 50.0379,
                        "lng": 8.5622,
                    },
                    "arrivalAirport": {
                        "iata": "JFK",
                        "icao": "KJFK",
                        "name": "JFK",
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
                },
                "Field required",
            ),
            # Invalid departureAirport IATA code (too short)
            (
                {
                    "flightNumber": "LH123",
                    "date": "2024-01-01",
                    "departureAirport": {
                        "iata": "FR",
                        "icao": "EDDF",
                        "name": "Frankfurt",
                        "city": "Frankfurt",
                        "country": "Germany",
                        "lat": 50.0379,
                        "lng": 8.5622,
                    },
                    "arrivalAirport": {
                        "iata": "JFK",
                        "icao": "KJFK",
                        "name": "JFK",
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
                },
                "at least 3 characters",
            ),
            # Invalid arrivalAirport lat (out of range)
            (
                {
                    "flightNumber": "LH123",
                    "date": "2024-01-01",
                    "departureAirport": {
                        "iata": "FRA",
                        "icao": "EDDF",
                        "name": "Frankfurt",
                        "city": "Frankfurt",
                        "country": "Germany",
                        "lat": 50.0379,
                        "lng": 8.5622,
                    },
                    "arrivalAirport": {
                        "iata": "JFK",
                        "icao": "KJFK",
                        "name": "JFK",
                        "city": "New York",
                        "country": "USA",
                        "lat": 100.0,
                        "lng": -73.7781,
                    },
                    "departureTime": "10:00",
                    "arrivalTime": "13:00",
                    "duration": "08:00",
                    "distance": 6200.0,
                    "airline": {"iata": "LH", "icao": "DLH", "name": "Lufthansa"},
                    "aircraft": {"icao": "A388", "name": "Airbus A380"},
                },
                "less than or equal to 90",
            ),
            # Invalid aircraft ICAO code (too short)
            (
                {
                    "flightNumber": "LH123",
                    "date": "2024-01-01",
                    "departureAirport": {
                        "iata": "FRA",
                        "icao": "EDDF",
                        "name": "Frankfurt",
                        "city": "Frankfurt",
                        "country": "Germany",
                        "lat": 50.0379,
                        "lng": 8.5622,
                    },
                    "arrivalAirport": {
                        "iata": "JFK",
                        "icao": "KJFK",
                        "name": "JFK",
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
                    "aircraft": {"icao": "A", "name": "Airbus A380"},
                },
                "at least 2 characters",
            ),
            # Invalid airline IATA code (too long)
            (
                {
                    "flightNumber": "LH123",
                    "date": "2024-01-01",
                    "departureAirport": {
                        "iata": "FRA",
                        "icao": "EDDF",
                        "name": "Frankfurt",
                        "city": "Frankfurt",
                        "country": "Germany",
                        "lat": 50.0379,
                        "lng": 8.5622,
                    },
                    "arrivalAirport": {
                        "iata": "JFK",
                        "icao": "KJFK",
                        "name": "JFK",
                        "city": "New York",
                        "country": "USA",
                        "lat": 40.6413,
                        "lng": -73.7781,
                    },
                    "departureTime": "10:00",
                    "arrivalTime": "13:00",
                    "duration": "08:00",
                    "distance": 6200.0,
                    "airline": {"iata": "LONG", "icao": "DLH", "name": "Lufthansa"},
                    "aircraft": {"icao": "A388", "name": "Airbus A380"},
                },
                "at most 2 characters",
            ),
        ],
    )
    def test_create_invalid_data(self, client, login_user, flight_data, expected_msg):
        token, user_id, email = login_user
        response = client.post(
            "/flights/",
            headers={"Authorization": f"Bearer {token}"},
            json=flight_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any(expected_msg in str(err["msg"]) for err in data["detail"])


class TestUpdateFlight:
    def test_update_flight(self, client, login_user):
        token, user_id, email = login_user

        # Create a flight to update
        flight_data = {
            "flightNumber": "LH123",
            "date": "2024-01-01",
            "departureAirport": {
                "iata": "FRA",
                "icao": "EDDF",
                "name": "Frankfurt",
                "city": "Frankfurt",
                "country": "Germany",
                "lat": 50.0379,
                "lng": 8.5622,
            },
            "arrivalAirport": {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "JFK",
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
        }
        response = client.post(
            "/flights/",
            headers={"Authorization": f"Bearer {token}"},
            json=flight_data,
        )
        assert response.status_code == 201
        created_flight = response.json()
        flight_id = created_flight["id"]

        # Update the flight
        update_data = {
            **flight_data,
            "flightNumber": "LH456",  # Change flight number
            "note": "Updated note",  # Add a note
        }
        response = client.put(
            f"/flights/{flight_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 200
        updated_flight = response.json()
        assert updated_flight["flightNumber"] == update_data["flightNumber"]
        assert updated_flight["note"] == update_data["note"]

        # Verify other fields remain unchanged
        for k, v in flight_data.items():
            if k not in ["flightNumber", "note"]:
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        assert updated_flight[k][subk] == subv
                else:
                    assert (
                        updated_flight[k] == v
                        or updated_flight[k] == v.upper()
                        or updated_flight[k] == v.capitalize()
                    )

        # Verify the updated flight can be retrieved
        response = client.get(
            f"/flights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        entities = data["entities"]
        flight = entities[0]
        assert flight["id"] == flight_id
        assert flight["flightNumber"] == update_data["flightNumber"]

    def test_update_invalid_token(self, client, login_user):
        token, user_id, email = login_user

        # Create a flight to update
        flight_data = {
            "flightNumber": "LH123",
            "date": "2024-01-01",
            "departureAirport": {
                "iata": "FRA",
                "icao": "EDDF",
                "name": "Frankfurt",
                "city": "Frankfurt",
                "country": "Germany",
                "lat": 50.0379,
                "lng": 8.5622,
            },
            "arrivalAirport": {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "JFK",
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
        }
        response = client.post(
            "/flights/",
            headers={"Authorization": f"Bearer {token}"},
            json=flight_data,
        )
        assert response.status_code == 201
        created_flight = response.json()
        flight_id = created_flight["id"]

        # Attempt to update with invalid token
        update_data = {
            **flight_data,
            "flightNumber": "LH456",
            "note": "Updated note",
        }
        response = client.put(
            f"/flights/{flight_id}",
            headers={"Authorization": "Bearer invalid_token"},
            json=update_data,
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_update_flight_not_found(self, client, login_user):
        token, user_id, email = login_user

        # Attempt to update a non-existing flight
        update_data = {
            "flightNumber": "LH456",
            "date": "2024-01-01",
            "departureAirport": {
                "iata": "FRA",
                "icao": "EDDF",
                "name": "Frankfurt",
                "city": "Frankfurt",
                "country": "Germany",
                "lat": 50.0379,
                "lng": 8.5622,
            },
            "arrivalAirport": {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "JFK",
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
        }
        response = client.put(
            "/flights/non_existing_id",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Flight" in data["detail"]


class TestDeleteFlight:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a flight to delete
        flight_data = {
            "flightNumber": "LH123",
            "date": "2024-01-01",
            "departureAirport": {
                "iata": "FRA",
                "icao": "EDDF",
                "name": "Frankfurt",
                "city": "Frankfurt",
                "country": "Germany",
                "lat": 50.0379,
                "lng": 8.5622,
            },
            "arrivalAirport": {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "JFK",
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
        }
        response = client.post(
            "/flights/",
            headers={"Authorization": f"Bearer {token}"},
            json=flight_data,
        )
        assert response.status_code == 201
        created_flight = response.json()
        flight_id = created_flight["id"]

        # Delete the flight
        response = client.delete(
            f"/flights/{flight_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == flight_id

        # Verify the flight is deleted
        response = client.get(
            f"/flights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 0

    def test_delete_invalid_token(self, client, login_user):
        token, user_id, email = login_user

        # Create a flight to delete
        flight_data = {
            "flightNumber": "LH123",
            "date": "2024-01-01",
            "departureAirport": {
                "iata": "FRA",
                "icao": "EDDF",
                "name": "Frankfurt",
                "city": "Frankfurt",
                "country": "Germany",
                "lat": 50.0379,
                "lng": 8.5622,
            },
            "arrivalAirport": {
                "iata": "JFK",
                "icao": "KJFK",
                "name": "JFK",
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
        }
        response = client.post(
            "/flights/",
            headers={"Authorization": f"Bearer {token}"},
            json=flight_data,
        )
        assert response.status_code == 201
        created_flight = response.json()
        flight_id = created_flight["id"]

        # Attempt to delete with invalid token
        response = client.delete(
            f"/flights/{flight_id}",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_delete_flight_not_found(self, client, login_user):
        token, user_id, email = login_user

        # Attempt to delete a non-existing flight
        response = client.delete(
            "/flights/non_existing_id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Flight" in data["detail"]


class TestQueryFlights:
    BASE_AIRPORT = {
        "iata": "XXX",
        "icao": "XXXX",
        "name": "Placeholder",
        "city": "Placeholder",
        "country": "Placeholder",
        "lat": 0.0,
        "lng": 0.0,
    }
    BASE_AIRLINE = {"iata": "XX", "icao": "XXX", "name": "Placeholder"}
    BASE_AIRCRAFT = {"icao": "B738", "name": "Boeing 737-800"}

    def _make_flight(self, overrides: dict) -> dict:
        base = {
            "flightNumber": "XX001",
            "date": "2024-01-01",
            "departureAirport": self.BASE_AIRPORT,
            "arrivalAirport": self.BASE_AIRPORT,
            "departureTime": "10:00",
            "arrivalTime": "12:00",
            "duration": "02:00",
            "distance": 1000.0,
            "airline": self.BASE_AIRLINE,
            "aircraft": self.BASE_AIRCRAFT,
            "seatType": "Aisle",
            "flightClass": "Economy",
            "flightReason": "Leisure",
            "isPlanned": False,
        }
        base.update(overrides)
        return base

    @pytest.fixture(autouse=True)
    def setup_flights(self, client, login_user):
        self.token, _, _ = login_user
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.client = client

        flights = [
            self._make_flight({
                "flightNumber": "LH100",
                "date": "2022-06-15",
                "departureAirport": {"iata": "FRA", "icao": "EDDF", "name": "Frankfurt", "city": "Frankfurt", "country": "Germany", "lat": 50.0379, "lng": 8.5622},
                "arrivalAirport": {"iata": "JFK", "icao": "KJFK", "name": "JFK", "city": "New York", "country": "USA", "lat": 40.6413, "lng": -73.7781},
                "distance": 6200.0,
                "airline": {"iata": "LH", "icao": "DLH", "name": "Lufthansa"},
                "aircraft": {"icao": "A388", "name": "Airbus A380"},
                "flightClass": "Business",
                "flightReason": "Business",
                "seatType": "Window",
                "isPlanned": False,
            }),
            self._make_flight({
                "flightNumber": "TK200",
                "date": "2023-03-20",
                "departureAirport": {"iata": "IST", "icao": "LTFM", "name": "Istanbul", "city": "Istanbul", "country": "Turkey", "lat": 41.2608, "lng": 28.7418},
                "arrivalAirport": {"iata": "ICN", "icao": "RKSI", "name": "Incheon", "city": "Seoul", "country": "Korea", "lat": 37.4691, "lng": 126.451},
                "distance": 8500.0,
                "airline": {"iata": "TK", "icao": "THY", "name": "Turkish Airlines"},
                "aircraft": {"icao": "B77W", "name": "Boeing 777-300ER"},
                "flightClass": "Economy",
                "flightReason": "Leisure",
                "seatType": "Aisle",
                "isPlanned": False,
            }),
            self._make_flight({
                "flightNumber": "QR300",
                "date": "2023-11-05",
                "departureAirport": {"iata": "DOH", "icao": "OTHH", "name": "Hamad", "city": "Doha", "country": "Qatar", "lat": 25.2731, "lng": 51.6081},
                "arrivalAirport": {"iata": "CDG", "icao": "LFPG", "name": "Charles de Gaulle", "city": "Paris", "country": "France", "lat": 49.0097, "lng": 2.5479},
                "distance": 7500.0,
                "airline": {"iata": "QR", "icao": "QTR", "name": "Qatar Airways"},
                "aircraft": {"icao": "A35K", "name": "Airbus A350-1000"},
                "flightClass": "Premium Economy",
                "flightReason": "Leisure",
                "seatType": "Middle",
                "isPlanned": False,
            }),
            self._make_flight({
                "flightNumber": "FR400",
                "date": "2024-08-10",
                "departureAirport": {"iata": "DUB", "icao": "EIDW", "name": "Dublin", "city": "Dublin", "country": "Ireland", "lat": 53.4213, "lng": -6.2701},
                "arrivalAirport": {"iata": "STN", "icao": "EGSS", "name": "Stansted", "city": "London", "country": "UK", "lat": 51.885, "lng": 0.235},
                "distance": 450.0,
                "airline": {"iata": "FR", "icao": "RYR", "name": "Ryanair"},
                "aircraft": {"icao": "B738", "name": "Boeing 737-800"},
                "flightClass": "Economy",
                "flightReason": "Leisure",
                "seatType": "Aisle",
                "isPlanned": True,
            }),
        ]
        for f in flights:
            client.post("/flights/", headers=self.headers, json=f)

    def _query(self, body: dict) -> list:
        response = self.client.post("/flights/query", headers=self.headers, json=body)
        assert response.status_code == 200
        return response.json()["entities"]

    def test_no_filters_returns_all(self):
        assert len(self._query({})) == 4

    def test_filter_by_year(self):
        entities = self._query({"year": ["2022"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "LH100"

    def test_filter_by_multiple_years(self):
        entities = self._query({"year": ["2022", "2023"]})
        assert len(entities) == 3

    def test_filter_by_is_planned(self):
        entities = self._query({"isPlanned": True})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "FR400"

    def test_filter_by_flight_class(self):
        entities = self._query({"flightClass": ["Business"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "LH100"

    def test_filter_by_multiple_flight_classes(self):
        entities = self._query({"flightClass": ["Economy", "Premium Economy"]})
        assert len(entities) == 3

    def test_filter_by_flight_reason(self):
        entities = self._query({"flightReason": ["Business"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "LH100"

    def test_filter_by_seat_type(self):
        entities = self._query({"seatType": ["Window"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "LH100"

    def test_filter_by_airline_iata(self):
        entities = self._query({"airlineIata": ["TK", "QR"]})
        assert len(entities) == 2

    def test_filter_by_aircraft_icao(self):
        entities = self._query({"aircraftIcao": ["B738"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "FR400"

    def test_filter_by_distance_gt(self):
        entities = self._query({"distanceGt": 7000.0})
        assert len(entities) == 2  # QR300 (7500) and TK200 (8500)

    def test_filter_by_distance_lt(self):
        entities = self._query({"distanceLt": 1000.0})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "FR400"

    def test_filter_by_distance_range(self):
        entities = self._query({"distanceGt": 400.0, "distanceLt": 6500.0})
        assert len(entities) == 2  # LH100 (6200) and FR400 (450)

    def test_filter_by_city_either(self):
        # Frankfurt is a departure city for LH100
        entities = self._query({"city": ["Frankfurt"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "LH100"

    def test_filter_by_city_matches_arrival(self):
        # Paris is an arrival city for QR300
        entities = self._query({"city": ["Paris"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "QR300"

    def test_filter_by_country_either(self):
        entities = self._query({"country": ["Korea"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "TK200"

    def test_filter_by_airport_iata_either(self):
        # ICN is arrival for TK200; CDG is arrival for QR300
        entities = self._query({"airportIata": ["ICN", "CDG"]})
        assert len(entities) == 2

    def test_filter_by_to_city(self):
        entities = self._query({"toCity": ["Seoul"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "TK200"

    def test_filter_by_to_country(self):
        entities = self._query({"toCountry": ["France"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "QR300"

    def test_filter_by_to_airport_iata(self):
        entities = self._query({"toAirportIata": ["STN"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "FR400"

    def test_filter_by_from_city(self):
        entities = self._query({"fromCity": ["Dublin"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "FR400"

    def test_filter_by_from_country(self):
        entities = self._query({"fromCountry": ["Turkey"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "TK200"

    def test_filter_by_from_airport_iata(self):
        entities = self._query({"fromAirportIata": ["DOH"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "QR300"

    def test_combined_filters(self):
        entities = self._query({"year": ["2023"], "flightClass": ["Economy"]})
        assert len(entities) == 1
        assert entities[0]["flightNumber"] == "TK200"

    def test_no_matches(self):
        entities = self._query({"year": ["1999"]})
        assert len(entities) == 0

    def test_invalid_token(self):
        response = self.client.post(
            "/flights/query",
            headers={"Authorization": "Bearer invalid_token"},
            json={},
        )
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    def test_invalid_year_format(self):
        response = self.client.post(
            "/flights/query",
            headers=self.headers,
            json={"year": ["not-a-year"]},
        )
        assert response.status_code == 422
