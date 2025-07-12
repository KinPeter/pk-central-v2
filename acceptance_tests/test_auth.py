import re
import time
from unittest.mock import MagicMock, patch
import pytest


class TestInstantLoginCode:
    def test_success(self, client, user_email):
        response = client.post(
            "/auth/instant-login-code",
            json={"email": user_email},
        )
        assert response.status_code == 201
        data = response.json()
        assert re.fullmatch(r"\d{6}", data["loginCode"])

    @pytest.mark.parametrize(
        "invalid_email",
        [
            "plainaddress",
            "missingatsign.com",
            "missingdomain@",
            "@missingusername.com",
            "user@.com",
        ],
    )
    def test_invalid_email_validation(self, client, invalid_email):
        response = client.post(
            "/auth/instant-login-code",
            json={"email": invalid_email},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "value is not a valid email address" in data["detail"][0]["msg"]


class TestPasswordSignup:
    def test_success(self, client, user_email):
        with patch(
            "app.modules.auth.password_signup.EmailManager"
        ) as mock_email_manager:
            mock_email_manager.return_value = MagicMock()
            response = client.post(
                "/auth/password-signup",
                json={"email": user_email, "password": "TestPassword123"},
            )
            assert response.status_code == 201
            data = response.json()
            assert "id" in data

    def test_email_already_exists(self, client, user_email):
        with patch(
            "app.modules.auth.password_signup.EmailManager"
        ) as mock_email_manager:
            mock_email_manager.return_value = MagicMock()
            # First signup to create the user
            response = client.post(
                "/auth/password-signup",
                json={"email": user_email, "password": "TestPassword123"},
            )
            assert response.status_code == 201

            # Try to sign up again with the same email
            response = client.post(
                "/auth/password-signup",
                json={"email": user_email, "password": "AnotherPassword123"},
            )
            assert response.status_code == 409
            data = response.json()
            assert "detail" in data
            assert "User with this email already exists" in data["detail"]


class TestPasswordLogin:
    def test_success(self, client, user_email):
        with patch(
            "app.modules.auth.password_signup.EmailManager"
        ) as mock_email_manager:
            mock_email_manager.return_value = MagicMock()
            # First signup to create the user
            response = client.post(
                "/auth/password-signup",
                json={"email": user_email, "password": "TestPassword123"},
            )
            assert response.status_code == 201

            # Now try to log in
            response = client.post(
                "/auth/password-login",
                json={"email": user_email, "password": "TestPassword123"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "token" in data

    def test_invalid_password(self, client, user_email):
        with patch(
            "app.modules.auth.password_signup.EmailManager"
        ) as mock_email_manager:
            mock_email_manager.return_value = MagicMock()
            # First signup to create the user
            response = client.post(
                "/auth/password-signup",
                json={"email": user_email, "password": "TestPassword123"},
            )
            assert response.status_code == 201

            # Try to log in with an invalid password
            response = client.post(
                "/auth/password-login",
                json={"email": user_email, "password": "WrongPassword"},
            )
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert "Invalid password" in data["detail"]

    def test_nonexistent_user(self, client, user_email):
        # Try to log in with a non-existent user
        response = client.post(
            "/auth/password-login",
            json={"email": user_email, "password": "TestPassword123"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid email or password" in data["detail"]


class TestRequestLoginCode:
    def test_success_signup(self, client, user_email):
        with patch(
            "app.modules.auth.request_login_code.EmailManager"
        ) as mock_email_manager:
            mock_email_manager.return_value = MagicMock()
            response = client.post(
                "/auth/login-code",
                json={"email": user_email},
            )
            assert response.status_code == 201
            data = response.json()
            assert "message" in data
            assert "Check your inbox" in data["message"]

    def test_success_login(self, client, user_email):
        with patch(
            "app.modules.auth.password_signup.EmailManager"
        ) as mock_email_manager1, patch(
            "app.modules.auth.request_login_code.EmailManager"
        ) as mock_email_manager2:
            mock_email_manager1.return_value = MagicMock()
            mock_email_manager2.return_value = MagicMock()
            # First signup to create the user
            response = client.post(
                "/auth/password-signup",
                json={"email": user_email, "password": "TestPassword123"},
            )
            assert response.status_code == 201

            # Now request a login code
            response = client.post(
                "/auth/login-code",
                json={"email": user_email},
            )
            assert response.status_code == 201
            data = response.json()
            assert "message" in data
            assert "Check your inbox" in data["message"]


class TestVerifyLoginCode:
    def test_success(self, client, user_email):
        # First request a login code
        response = client.post(
            "/auth/instant-login-code",
            json={"email": user_email},
        )
        assert response.status_code == 201

        # Now verify the login code
        response = client.post(
            "/auth/verify-login-code",
            json={"email": user_email, "loginCode": response.json()["loginCode"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data

    def test_invalid_code(self, client, user_email):
        # First request a login code
        response = client.post(
            "/auth/instant-login-code",
            json={"email": user_email},
        )
        assert response.status_code == 201

        # Now try to verify with an invalid code
        response = client.post(
            "/auth/verify-login-code",
            json={"email": user_email, "loginCode": "123456"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid login code" in data["detail"]

    def test_nonexistent_user(self, client, user_email):
        # Try to verify a login code for a non-existent user
        response = client.post(
            "/auth/verify-login-code",
            json={"email": user_email, "loginCode": "123456"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid email or login code" in data["detail"]


class TestTokenRefresh:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Ensure the new token is generated after a short delay
        time.sleep(2)

        response = client.post(
            "/auth/token-refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "expiresAt" in data
        assert data["token"] != token
        assert data["id"] == user_id
        assert data["email"] == email

    def test_invalid_token(self, client):
        response = client.post(
            "/auth/token-refresh",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]


class TestSetPassword:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        response = client.post(
            "/auth/set-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": email, "password": "NewPassword123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["id"] == user_id

        response = client.post(
            "/auth/password-login",
            json={"email": email, "password": "NewPassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data

    def test_invalid_token(self, client):
        response = client.post(
            "/auth/set-password",
            headers={"Authorization": "Bearer invalid_token"},
            json={"password": "NewPassword123"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_too_short_password(self, client, login_user):
        token, user_id, email = login_user

        response = client.post(
            "/auth/set-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": email, "password": "short"},
        )
        assert response.status_code == 422


class TestInitialUserConfigCreation:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Patch the env object on the app
        client.app.state.env.OPEN_WEATHER_MAP_API_KEY = "test-owm-key"
        client.app.state.env.LOCATION_IQ_API_KEY = "test-liq-key"
        client.app.state.env.UNSPLASH_API_KEY = "test-unspl-key"
        client.app.state.env.STRAVA_CLIENT_ID = "test-strava-id"
        client.app.state.env.STRAVA_CLIENT_SECRET = "test-strava-secret"

        # Reddit config
        response = client.get(
            "/reddit/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sets" in data
        assert "blockedUsers" in data
        assert len(data["sets"]) == 1
        assert data["sets"][0]["name"] == "Default"
        assert data["sets"][0]["subs"] == []
        assert data["sets"][0]["usernames"] == []

        # Start settings
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

        # Activities config
        response = client.get(
            "/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["chores"] == []
        assert data["walkWeeklyGoal"] == 0
        assert data["walkMonthlyGoal"] == 0
        assert data["cyclingWeeklyGoal"] == 0
        assert data["cyclingMonthlyGoal"] == 0
