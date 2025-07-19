from unittest.mock import AsyncMock, patch


class TestGetAirportData:
    @patch("app.modules.trips.airports.GeminiApi")
    def test_success_from_db(self, mock_gemini_api, client, login_user):
        mock_gemini_api.return_value.generate_json = AsyncMock(return_value={...})
        token, user_id, email = login_user
        response = client.get(
            "/trips/airports/?iata=BUD",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["iata"] == "BUD"
        assert data["icao"] == "LHBP"
        assert data["name"] == "Db Test Liszt Ferenc International Airport"
        assert data["city"] == "Budapest"
        assert data["country"] == "Hungary"
        assert data["lat"] == 47.4369
        assert data["lng"] == 19.2556

    @patch("app.modules.trips.airports.GeminiApi")
    def test_success_from_gemini(self, mock_gemini_api, client, login_user):
        mock_gemini_api.return_value.generate_json = AsyncMock(
            return_value={
                "iata": "CPH",
                "icao": "EKCH",
                "name": "AI Test Kastrup Airport",
                "city": "Copenhagen",
                "country": "Denmark",
                "lat": 55.617,
                "lng": 12.6561,
            }
        )
        token, user_id, email = login_user
        response = client.get(
            "/trips/airports/?iata=CPH",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["iata"] == "CPH"
        assert data["icao"] == "EKCH"
        assert data["name"] == "AI Test Kastrup Airport"
        assert data["city"] == "Copenhagen"
        assert data["country"] == "Denmark"
        assert data["lat"] == 55.617
        assert data["lng"] == 12.6561

    def test_invalid_iata_code(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/trips/airports/?iata=INVALID",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "String should match pattern" in str(data["detail"])

    def test_invalid_token(self, client):
        response = client.get(
            "/trips/airports/?iata=BUD",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]
