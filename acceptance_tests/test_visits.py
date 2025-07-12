import pytest


class TestCreateAndGetVisits:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a visit
        visit_data = {
            "city": "Paris",
            "country": "France",
            "lat": 48.8566,
            "lng": 2.3522,
            "year": "2022",
        }
        response = client.post(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
            json=visit_data,
        )
        assert response.status_code == 201
        created_visit = response.json()
        assert created_visit["city"] == visit_data["city"]
        assert created_visit["country"] == visit_data["country"]
        assert created_visit["lat"] == visit_data["lat"]
        assert created_visit["lng"] == visit_data["lng"]
        assert created_visit["year"] == visit_data["year"]

        # Create another visit (no year)
        visit_data2 = {
            "city": "London",
            "country": "UK",
            "lat": 51.5074,
            "lng": -0.1278,
        }
        response = client.post(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
            json=visit_data2,
        )
        assert response.status_code == 201
        created_visit2 = response.json()
        assert created_visit2["city"] == visit_data2["city"]
        assert created_visit2["country"] == visit_data2["country"]
        assert created_visit2["lat"] == visit_data2["lat"]
        assert created_visit2["lng"] == visit_data2["lng"]
        assert created_visit2["year"] is None

        # Get all visits
        response = client.get(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        entities = data["entities"]
        assert len(entities) == 2
        assert entities[0]["city"] == visit_data["city"]
        assert entities[0]["country"] == visit_data["country"]
        assert entities[0]["lat"] == visit_data["lat"]
        assert entities[0]["lng"] == visit_data["lng"]
        assert entities[0]["year"] == visit_data["year"]
        assert entities[1]["city"] == visit_data2["city"]
        assert entities[1]["country"] == visit_data2["country"]
        assert entities[1]["lat"] == visit_data2["lat"]
        assert entities[1]["lng"] == visit_data2["lng"]
        assert entities[1]["year"] is None

    def test_create_invalid_token(self, client, login_user):
        # Create with invalid token
        response = client.post(
            "/visits/",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "city": "Paris",
                "country": "France",
                "lat": 48.8566,
                "lng": 2.3522,
                "year": "2022",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_get_visits_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        visit_data = {
            "city": "Paris",
            "country": "France",
            "lat": 48.8566,
            "lng": 2.3522,
        }
        response = client.post(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
            json=visit_data,
        )
        assert response.status_code == 201
        # Get with invalid token
        response = client.get(
            "/visits/",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "visit_data,expected_msg",
        [
            # Invalid year
            (
                {
                    "city": "Paris",
                    "country": "France",
                    "lat": 48.8566,
                    "lng": 2.3522,
                    "year": "not-a-year",
                },
                "String should match pattern",
            ),
            # City too short
            (
                {"city": "", "country": "France", "lat": 48.8566, "lng": 2.3522},
                "at least 1 character",
            ),
            # City too long
            (
                {"city": "a" * 101, "country": "France", "lat": 48.8566, "lng": 2.3522},
                "at most 100 characters",
            ),
            # Country too short
            (
                {"city": "Paris", "country": "", "lat": 48.8566, "lng": 2.3522},
                "at least 1 character",
            ),
            # Country too long
            (
                {"city": "Paris", "country": "a" * 101, "lat": 48.8566, "lng": 2.3522},
                "at most 100 characters",
            ),
            # Latitude out of range
            (
                {"city": "Paris", "country": "France", "lat": 100.0, "lng": 2.3522},
                "less than or equal to 90",
            ),
            # Longitude out of range
            (
                {"city": "Paris", "country": "France", "lat": 48.8566, "lng": 200.0},
                "less than or equal to 180",
            ),
            # Missing required fields
            (
                {"country": "France", "lat": 48.8566, "lng": 2.3522},
                "Field required",
            ),
            (
                {"city": "Paris", "lat": 48.8566, "lng": 2.3522},
                "Field required",
            ),
            (
                {"city": "Paris", "country": "France", "lng": 2.3522},
                "Field required",
            ),
            (
                {"city": "Paris", "country": "France", "lat": 48.8566},
                "Field required",
            ),
        ],
    )
    def test_create_invalid_data(self, client, login_user, visit_data, expected_msg):
        token, user_id, email = login_user
        response = client.post(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
            json=visit_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestUpdateVisit:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        # Create first
        visit_data = {
            "city": "Paris",
            "country": "France",
            "lat": 48.8566,
            "lng": 2.3522,
        }
        response = client.post(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
            json=visit_data,
        )
        assert response.status_code == 201
        created_visit = response.json()
        visit_id = created_visit["id"]
        # Update
        update_data = {
            "city": "Paris Updated",
            "country": "France",
            "lat": 48.9,
            "lng": 2.4,
            "year": "2025",
        }
        response = client.put(
            f"/visits/{visit_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 200
        updated_visit = response.json()
        assert updated_visit["city"] == update_data["city"]
        assert updated_visit["country"] == update_data["country"]
        assert updated_visit["lat"] == update_data["lat"]
        assert updated_visit["lng"] == update_data["lng"]
        assert updated_visit["year"] == update_data["year"]
        # Get all to verify
        response = client.get(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert any(
            e["id"] == visit_id and e["city"] == update_data["city"] for e in entities
        )

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        visit_data = {
            "city": "Paris",
            "country": "France",
            "lat": 48.8566,
            "lng": 2.3522,
        }
        response = client.post(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
            json=visit_data,
        )
        assert response.status_code == 201
        visit_id = response.json()["id"]
        update_data = {
            "city": "Paris Updated",
            "country": "France",
            "lat": 48.9,
            "lng": 2.4,
        }
        response = client.put(
            f"/visits/{visit_id}",
            headers={"Authorization": "Bearer invalid_token"},
            json=update_data,
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_visit(self, client, login_user):
        token, user_id, email = login_user
        update_data = {
            "city": "Paris Updated",
            "country": "France",
            "lat": 48.9,
            "lng": 2.4,
        }
        response = client.put(
            "/visits/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Visit" in data["detail"]

    @pytest.mark.parametrize(
        "update_data,expected_msg",
        [
            # Invalid year
            (
                {
                    "city": "Paris",
                    "country": "France",
                    "lat": 48.8566,
                    "lng": 2.3522,
                    "year": "not-a-year",
                },
                "String should match pattern",
            ),
            # City too short
            (
                {"city": "", "country": "France", "lat": 48.8566, "lng": 2.3522},
                "at least 1 character",
            ),
            # City too long
            (
                {"city": "a" * 101, "country": "France", "lat": 48.8566, "lng": 2.3522},
                "at most 100 characters",
            ),
            # Country too short
            (
                {"city": "Paris", "country": "", "lat": 48.8566, "lng": 2.3522},
                "at least 1 character",
            ),
            # Country too long
            (
                {"city": "Paris", "country": "a" * 101, "lat": 48.8566, "lng": 2.3522},
                "at most 100 characters",
            ),
            # Latitude out of range
            (
                {"city": "Paris", "country": "France", "lat": 100.0, "lng": 2.3522},
                "less than or equal to 90",
            ),
            # Longitude out of range
            (
                {"city": "Paris", "country": "France", "lat": 48.8566, "lng": 200.0},
                "less than or equal to 180",
            ),
            # Latitude string
            (
                {
                    "city": "Paris",
                    "country": "France",
                    "lat": "not-float",
                    "lng": 2.3522,
                },
                "Input should be a valid number",
            ),
            # Longitude string
            (
                {
                    "city": "Paris",
                    "country": "France",
                    "lat": 48.8566,
                    "lng": "not-float",
                },
                "Input should be a valid number",
            ),
            # Missing required fields
            (
                {"country": "France", "lat": 48.8566, "lng": 2.3522},
                "Field required",
            ),
            (
                {"city": "Paris", "lat": 48.8566, "lng": 2.3522},
                "Field required",
            ),
            (
                {"city": "Paris", "country": "France", "lng": 2.3522},
                "Field required",
            ),
            (
                {"city": "Paris", "country": "France", "lat": 48.8566},
                "Field required",
            ),
        ],
    )
    def test_invalid_data(self, client, login_user, update_data, expected_msg):
        token, user_id, email = login_user
        visit_data = {
            "city": "Paris",
            "country": "France",
            "lat": 48.8566,
            "lng": 2.3522,
        }
        response = client.post(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
            json=visit_data,
        )
        assert response.status_code == 201
        visit_id = response.json()["id"]
        response = client.put(
            f"/visits/{visit_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestDeleteVisit:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        visit_data = {"city": "To Delete", "country": "Nowhere", "lat": 0.0, "lng": 0.0}
        response = client.post(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
            json=visit_data,
        )
        assert response.status_code == 201
        visit_id = response.json()["id"]
        response = client.delete(
            f"/visits/{visit_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == visit_id

        # Verify deletion
        response = client.get(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert all(e["id"] != visit_id for e in entities)

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        visit_data = {"city": "To Delete", "country": "Nowhere", "lat": 0.0, "lng": 0.0}
        response = client.post(
            "/visits/",
            headers={"Authorization": f"Bearer {token}"},
            json=visit_data,
        )
        assert response.status_code == 201
        visit_id = response.json()["id"]
        response = client.delete(
            f"/visits/{visit_id}",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_visit(self, client, login_user):
        token, user_id, email = login_user
        response = client.delete(
            "/visits/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Visit" in data["detail"]
