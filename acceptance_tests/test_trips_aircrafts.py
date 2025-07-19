class TestSearchAircrafts:
    def test_success_by_icao(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/trips/aircrafts?search=A320",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["icao"] == "A320"
        assert data["entities"][0]["name"] == "Db Test Airbus A320"

    def test_success_by_name(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/trips/aircrafts?search=Airbus",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["icao"] == "A320"
        assert data["entities"][0]["name"] == "Db Test Airbus A320"

    def test_invalid_token(self, client):
        response = client.get(
            "/trips/aircrafts?search=A320",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_no_results(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/trips/aircrafts?search=NonExistentAircraft",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 0
