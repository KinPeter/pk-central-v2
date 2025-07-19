class TestSearchAirlines:
    def test_success_by_iata(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/trips/airlines?iata=5P",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["iata"] == "5P"
        assert data["entities"][0]["icao"] == "HSK"
        assert data["entities"][0]["name"] == "Db Test SkyEurope Airlines"

    def test_success_by_name(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/trips/airlines?name=skyeu",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["iata"] == "5P"
        assert data["entities"][0]["icao"] == "HSK"
        assert data["entities"][0]["name"] == "Db Test SkyEurope Airlines"

    def test_no_results(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/trips/airlines?iata=xx",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 0

    def test_invalid_iata_code(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/trips/airlines?iata=INVALID",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "String should match pattern" in str(data["detail"])

    def test_invalid_name(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/trips/airlines?name=A",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "at least 2 characters" in str(data["detail"])

    def test_invalid_token(self, client):
        response = client.get(
            "/trips/airlines?iata=5P",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]
