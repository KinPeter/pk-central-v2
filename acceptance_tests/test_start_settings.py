import pytest


class TestUpdateAndGetStartSettings:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Patch the env object on the app
        client.app.state.env.OPEN_WEATHER_MAP_API_KEY = "test-owm-key"
        client.app.state.env.LOCATION_IQ_API_KEY = "test-liq-key"
        client.app.state.env.UNSPLASH_API_KEY = "test-unspl-key"
        client.app.state.env.STRAVA_CLIENT_ID = "test-strava-id"
        client.app.state.env.STRAVA_CLIENT_SECRET = "test-strava-secret"

        # Get initial start settings
        response = client.get(
            "/start-settings/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] is None
        assert data["shortcutIconBaseUrl"] is None
        assert data["stravaRedirectUri"] is None
        assert data["openWeatherApiKey"] == "test-owm-key"
        assert data["locationIqApiKey"] == "test-liq-key"
        assert data["unsplashApiKey"] == "test-unspl-key"
        assert data["stravaClientId"] == "test-strava-id"
        assert data["stravaClientSecret"] == "test-strava-secret"

        # Update start settings
        update_data = {
            "name": "My Start Settings",
            "shortcutIconBaseUrl": "http://icons/",
            "stravaRedirectUri": "http://strava/",
        }
        response = client.put(
            "/start-settings/",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 200
        updated_data = response.json()
        assert updated_data["name"] == "My Start Settings"
        assert updated_data["shortcutIconBaseUrl"] == "http://icons/"
        assert updated_data["stravaRedirectUri"] == "http://strava/"
        assert updated_data["id"] == data["id"]
        assert data["openWeatherApiKey"] == "test-owm-key"
        assert data["locationIqApiKey"] == "test-liq-key"
        assert data["unsplashApiKey"] == "test-unspl-key"
        assert data["stravaClientId"] == "test-strava-id"
        assert data["stravaClientSecret"] == "test-strava-secret"

        # Get again to verify update
        response = client.get(
            "/start-settings/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        final_data = response.json()
        assert final_data["name"] == "My Start Settings"
        assert final_data["shortcutIconBaseUrl"] == "http://icons/"
        assert final_data["stravaRedirectUri"] == "http://strava/"
        assert final_data["id"] == data["id"]
        assert data["openWeatherApiKey"] == "test-owm-key"
        assert data["locationIqApiKey"] == "test-liq-key"
        assert data["unsplashApiKey"] == "test-unspl-key"
        assert data["stravaClientId"] == "test-strava-id"
        assert data["stravaClientSecret"] == "test-strava-secret"

    def test_update_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        update_data = {"name": "Should Fail"}
        response = client.put(
            "/start-settings/",
            headers={"Authorization": f"Bearer wrong_token"},
            json=update_data,
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "invalid_update_data,expected_type,expected_msg",
        [
            ({"name": 12345}, "str", "string"),
            ({"shortcutIconBaseUrl": "not-a-url"}, "url", "url"),
            ({"stravaRedirectUri": 12345}, "url", "url"),
            ({"shortcutIconBaseUrl": 12345}, "url", "url"),
        ],
    )
    def test_update_invalid_data(
        self, client, login_user, invalid_update_data, expected_type, expected_msg
    ):
        token, user_id, email = login_user
        response = client.put(
            "/start-settings/",
            headers={"Authorization": f"Bearer {token}"},
            json=invalid_update_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert (
            expected_type in data["detail"][0]["type"]
            or expected_msg in data["detail"][0]["msg"].lower()
        )
