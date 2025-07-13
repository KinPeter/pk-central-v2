import pytest
import respx
from httpx import Response


class TestProxyLocationCity:
    @respx.mock
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Mock the LocationIQ API endpoint
        respx.get("https://eu1.locationiq.com/v1/reverse").mock(
            return_value=Response(
                200,
                json={"address": {"city": "Beerlin", "country_code": "DE"}},
            )
        )

        response = client.get(
            "/proxy/location/city?lat=52.52&lng=13.405",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Beerlin"
        assert data["country"] == "Germany"
        assert data["lat"] == 52.52
        assert data["lng"] == 13.405

    @respx.mock
    def test_invalid_token(self, client):
        respx.get("https://eu1.locationiq.com/v1/reverse").mock(
            return_value=Response(
                200,
                json={"address": {"city": "Berlin", "country_code": "DE"}},
            )
        )
        response = client.get(
            "/proxy/location/city?lat=52.52&lng=13.405",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "params,expected_msg",
        [
            ("?lng=13.405", "Field required"),  # Missing lat
            ("?lat=52.52", "Field required"),  # Missing lng
            ("", "Field required"),  # Missing both
            ("?lat=abc&lng=13.405", "Input should be a valid number"),
            ("?lat=52.52&lng=xyz", "Input should be a valid number"),
        ],
    )
    @respx.mock
    def test_invalid_request(self, client, login_user, params, expected_msg):
        token, user_id, email = login_user
        respx.get("https://eu1.locationiq.com/v1/reverse").mock(
            return_value=Response(
                200,
                json={"address": {"city": "Berlin", "country_code": "DE"}},
            )
        )
        response = client.get(
            f"/proxy/location/city{params}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]

    @respx.mock
    def test_locationiq_api_error(self, client, login_user):
        token, user_id, email = login_user
        # Mock the LocationIQ API endpoint to return a 500 error
        respx.get("https://eu1.locationiq.com/v1/reverse").mock(
            return_value=Response(500, json={"error": "Internal Server Error"})
        )

        response = client.get(
            "/proxy/location/city?lat=52.52&lng=13.405",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Internal Server Error" in data["detail"]
        assert "Failed to retrieve city location" in data["detail"]
