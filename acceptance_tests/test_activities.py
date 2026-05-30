import pytest
import respx
from httpx import Response

# Parametrize cases covering all invalid auth scenarios for endpoints that
# support both Bearer token and API key authentication.
AUTH_ERROR_CASES = [
    pytest.param({}, id="no_auth"),
    pytest.param({"X-PK-Api-Key": "pk_invalid_key"}, id="invalid_api_key"),
    pytest.param({"Authorization": "Bearer invalid.jwt.token"}, id="invalid_bearer"),
]


class TestUpdateGoals:
    def test_update_goals_success(self, client, login_user):
        token, user_id, email = login_user

        # Getting initial config
        response = client.get(
            "/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert data["walkWeeklyGoal"] == 0
        assert data["walkMonthlyGoal"] == 0
        assert data["cyclingWeeklyGoal"] == 0
        assert data["cyclingMonthlyGoal"] == 0
        assert data["stepsWeeklyGoal"] == 0
        assert data["stepsMonthlyGoal"] == 0

        # Updating goals
        body = {
            "walkWeeklyGoal": 1000,
            "walkMonthlyGoal": 4000,
            "cyclingWeeklyGoal": 200,
            "cyclingMonthlyGoal": 800,
            "stepsWeeklyGoal": 35000,
            "stepsMonthlyGoal": 140000,
        }
        response = client.patch(
            "/activities/goals", headers={"Authorization": f"Bearer {token}"}, json=body
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert data["walkWeeklyGoal"] == 1000
        assert data["walkMonthlyGoal"] == 4000
        assert data["cyclingWeeklyGoal"] == 200
        assert data["cyclingMonthlyGoal"] == 800
        assert data["stepsWeeklyGoal"] == 35000
        assert data["stepsMonthlyGoal"] == 140000
        assert data["chores"] == []

        # Verifying the updated config
        response = client.get(
            "/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert data["walkWeeklyGoal"] == 1000
        assert data["walkMonthlyGoal"] == 4000
        assert data["cyclingWeeklyGoal"] == 200
        assert data["cyclingMonthlyGoal"] == 800
        assert data["stepsWeeklyGoal"] == 35000
        assert data["stepsMonthlyGoal"] == 140000
        assert data["chores"] == []

    @pytest.mark.parametrize(
        "body,expected_status",
        [
            ({}, 422),  # All fields missing
            (
                {
                    "walkWeeklyGoal": -1,
                    "walkMonthlyGoal": 0,
                    "cyclingWeeklyGoal": 0,
                    "cyclingMonthlyGoal": 0,
                },
                422,
            ),  # Negative value
            (
                {
                    "walkWeeklyGoal": 1000,
                    "walkMonthlyGoal": "bad",
                    "cyclingWeeklyGoal": 0,
                    "cyclingMonthlyGoal": 0,
                },
                422,
            ),  # Wrong type
            (
                {
                    "walkWeeklyGoal": 1000,
                    "cyclingWeeklyGoal": 0,
                    "cyclingMonthlyGoal": 0,
                },
                422,
            ),  # Missing walkMonthlyGoal
            (
                {
                    "walkWeeklyGoal": 1000,
                    "walkMonthlyGoal": 4000,
                    "cyclingWeeklyGoal": 0,
                },
                422,
            ),  # Missing cyclingMonthlyGoal
            (
                {
                    "walkWeeklyGoal": 1000,
                    "walkMonthlyGoal": 4000,
                    "cyclingWeeklyGoal": 100,
                    "cyclingMonthlyGoal": 400,
                    "stepsWeeklyGoal": -5000,
                },
                422,
            ),  # Negative stepsWeeklyGoal
            (
                {
                    "walkWeeklyGoal": 1000,
                    "walkMonthlyGoal": 4000,
                    "cyclingWeeklyGoal": 100,
                    "cyclingMonthlyGoal": 400,
                    "stepsMonthlyGoal": -20000,
                },
                422,
            ),  # Negative stepsMonthlyGoal
        ],
    )
    def test_update_goals_invalid_body(self, client, login_user, body, expected_status):
        token, *_ = login_user
        response = client.patch(
            "/activities/goals", headers={"Authorization": f"Bearer {token}"}, json=body
        )
        assert response.status_code == expected_status
        # Optionally, check error message structure
        if expected_status == 422:
            data = response.json()
            assert "detail" in data

    def test_get_activities_with_api_key(self, client, api_key):
        response = client.get(
            "/activities",
            headers={"X-PK-Api-Key": api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None

    def test_update_goals_with_api_key(self, client, api_key):
        body = {
            "walkWeeklyGoal": 500,
            "walkMonthlyGoal": 2000,
            "cyclingWeeklyGoal": 100,
            "cyclingMonthlyGoal": 400,
            "stepsWeeklyGoal": 35000,
            "stepsMonthlyGoal": 140000,
        }
        response = client.patch(
            "/activities/goals",
            headers={"X-PK-Api-Key": api_key},
            json=body,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["walkWeeklyGoal"] == 500
        assert data["walkMonthlyGoal"] == 2000
        assert data["cyclingWeeklyGoal"] == 100
        assert data["cyclingMonthlyGoal"] == 400
        assert data["stepsWeeklyGoal"] == 35000
        assert data["stepsMonthlyGoal"] == 140000

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_get_activities_auth_errors(self, client, headers):
        response = client.get("/activities", headers=headers)
        assert response.status_code == 401

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_update_goals_auth_errors(self, client, headers):
        body = {
            "walkWeeklyGoal": 1000,
            "walkMonthlyGoal": 4000,
            "cyclingWeeklyGoal": 200,
            "cyclingMonthlyGoal": 800,
            "stepsWeeklyGoal": 35000,
            "stepsMonthlyGoal": 140000,
        }
        response = client.patch("/activities/goals", headers=headers, json=body)
        assert response.status_code == 401


class TestAddChore:
    def test_add_chore_success(self, client, login_user):
        token, user_id, email = login_user

        # Getting initial config
        response = client.get(
            "/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert data["chores"] == []

        # Adding a chore
        body = {
            "name": "Test Chore",
            "kmInterval": 30,
            "lastKm": 0.0,
        }
        response = client.post(
            "/activities/chores",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert len(data["chores"]) == 1
        chore = data["chores"][0]
        assert chore["name"] == "Test Chore"
        assert chore["kmInterval"] == 30
        assert chore["lastKm"] == 0.0

        # Verifying the updated config
        response = client.get(
            "/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert len(data["chores"]) == 1
        chore = data["chores"][0]
        assert chore["name"] == "Test Chore"
        assert chore["kmInterval"] == 30
        assert chore["lastKm"] == 0.0

    @pytest.mark.parametrize(
        "body,expected_status",
        [
            ({}, 422),  # All fields missing
            ({"name": "Chore"}, 422),  # Missing kmInterval and lastKm
            ({"kmInterval": 30, "lastKm": 10.5}, 422),  # Missing name
            (
                {"name": "Chore", "kmInterval": -10, "lastKm": 10.5},
                422,
            ),  # Negative kmInterval
            (
                {"name": "Chore", "kmInterval": "bad", "lastKm": 10.5},
                422,
            ),  # Wrong type for kmInterval
            (
                {"name": "Chore", "kmInterval": 30, "lastKm": "bad"},
                422,
            ),  # Wrong type for lastKm
        ],
    )
    def test_add_chore_invalid_body(self, client, login_user, body, expected_status):
        token, *_ = login_user
        response = client.post(
            "/activities/chores",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
        )
        assert response.status_code == expected_status
        # Optionally, check error message structure
        if expected_status == 422:
            data = response.json()
            assert "detail" in data and isinstance(data["detail"], list)

    def test_add_chore_with_api_key(self, client, api_key):
        body = {
            "name": "API Key Chore",
            "kmInterval": 30,
            "lastKm": 0.0,
        }
        response = client.post(
            "/activities/chores",
            headers={"X-PK-Api-Key": api_key},
            json=body,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["chores"]) == 1
        chore = data["chores"][0]
        assert chore["name"] == "API Key Chore"
        assert chore["kmInterval"] == 30
        assert chore["lastKm"] == 0.0

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_add_chore_auth_errors(self, client, headers):
        body = {
            "name": "Test Chore",
            "kmInterval": 30,
            "lastKm": 0.0,
        }
        response = client.post("/activities/chores", headers=headers, json=body)
        assert response.status_code == 401


class TestUpdateChore:
    def test_update_chore_success(self, client, login_user):
        token, user_id, email = login_user

        # Adding a chore first
        body = {
            "name": "Initial Chore",
            "kmInterval": 50,
            "lastKm": 10.0,
        }
        response = client.post(
            "/activities/chores",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
        )
        assert response.status_code == 201
        data = response.json()
        chore_id = data["chores"][0]["id"]

        # Updating the chore
        update_body = {
            "name": "Updated Chore",
            "kmInterval": 100,
            "lastKm": 123.4,
        }
        response = client.put(
            f"/activities/chores/{chore_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_body,
        )
        assert response.status_code == 200
        updated_data = response.json()
        assert updated_data["id"] is not None
        assert len(updated_data["chores"]) == 1
        chore = updated_data["chores"][0]
        assert chore["id"] == chore_id
        assert chore["name"] == "Updated Chore"
        assert chore["kmInterval"] == 100
        assert chore["lastKm"] == 123.4

    @pytest.mark.parametrize(
        "chore_id,update_body,expected_status",
        [
            (
                "invalid-id",
                {"name": "Chore", "kmInterval": 32, "lastKm": 123.3},
                404,
            ),  # Invalid ID
            (
                "",
                {"name": "Chore"},
                405,
            ),  # Empty ID - this should be a 405 Method Not Allowed
            ("valid-id", {}, 422),  # No fields to update
            (
                "valid-id",
                {"name": "", "kmInterval": 200, "lastKm": 321},
                422,
            ),  # Empty name
            (
                "valid-id",
                {"name": "A name", "kmInterval": -10, "lastKm": 321},
                422,
            ),  # Negative kmInterval
            (
                "valid-id",
                {"name": "A name", "kmInterval": "bad", "lastKm": 321},
                422,
            ),  # Wrong type for kmInterval
            (
                "valid-id",
                {"name": "A name", "kmInterval": 200, "lastKm": "bad"},
                422,
            ),  # Wrong type for lastKm
        ],
    )
    def test_update_chore_invalid_cases(
        self, client, login_user, chore_id, update_body, expected_status
    ):
        token, *_ = login_user
        if chore_id == "valid-id":
            # Adding a chore first to get a valid ID
            body = {
                "name": "Initial Chore",
                "kmInterval": 50,
                "lastKm": 10.0,
            }
            response = client.post(
                "/activities/chores",
                headers={"Authorization": f"Bearer {token}"},
                json=body,
            )
            assert response.status_code == 201
            data = response.json()
            chore_id = data["chores"][0]["id"]
        response = client.put(
            f"/activities/chores/{chore_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_body,
        )
        assert response.status_code == expected_status
        # Optionally, check error message structure
        if expected_status == 422:
            data = response.json()
            assert "detail" in data and isinstance(data["detail"], list)

        if expected_status == 404:
            data = response.json()
            assert "detail" in data
            assert "Not Found: Chore" in data["detail"]

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_update_chore_auth_errors(self, client, headers):
        # Auth is checked before resource lookup, so the chore ID doesn't need to exist
        body = {"name": "Chore", "kmInterval": 50, "lastKm": 0.0}
        response = client.put(
            "/activities/chores/some-chore-id", headers=headers, json=body
        )
        assert response.status_code == 401

    def test_update_chore_with_api_key(self, client, api_key):
        # Create a chore using the api key
        body = {
            "name": "Initial Chore",
            "kmInterval": 50,
            "lastKm": 10.0,
        }
        response = client.post(
            "/activities/chores",
            headers={"X-PK-Api-Key": api_key},
            json=body,
        )
        assert response.status_code == 201
        chore_id = response.json()["chores"][0]["id"]

        # Update the chore using the api key
        update_body = {
            "name": "Updated via API Key",
            "kmInterval": 100,
            "lastKm": 200.0,
        }
        response = client.put(
            f"/activities/chores/{chore_id}",
            headers={"X-PK-Api-Key": api_key},
            json=update_body,
        )
        assert response.status_code == 200
        chore = response.json()["chores"][0]
        assert chore["id"] == chore_id
        assert chore["name"] == "Updated via API Key"
        assert chore["kmInterval"] == 100
        assert chore["lastKm"] == 200.0


class TestDeleteChore:
    def test_delete_chore_success(self, client, login_user):
        token, user_id, email = login_user

        # Adding a chore first
        body = {
            "name": "Chore to Delete",
            "kmInterval": 50,
            "lastKm": 10.0,
        }
        response = client.post(
            "/activities/chores",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["chores"]) == 1
        chore_id = data["chores"][0]["id"]

        # Deleting the chore
        response = client.delete(
            f"/activities/chores/{chore_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["chores"]) == 0

        # Verifying the chore is deleted
        response = client.get(
            "/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["chores"]) == 0

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_delete_chore_auth_errors(self, client, headers):
        # Auth is checked before resource lookup, so the chore ID doesn't need to exist
        response = client.delete("/activities/chores/some-chore-id", headers=headers)
        assert response.status_code == 401

    def test_delete_chore_with_api_key(self, client, api_key):
        # Create a chore using the api key
        body = {
            "name": "Chore to Delete",
            "kmInterval": 50,
            "lastKm": 10.0,
        }
        response = client.post(
            "/activities/chores",
            headers={"X-PK-Api-Key": api_key},
            json=body,
        )
        assert response.status_code == 201
        chore_id = response.json()["chores"][0]["id"]

        # Delete the chore using the api key
        response = client.delete(
            f"/activities/chores/{chore_id}",
            headers={"X-PK-Api-Key": api_key},
        )
        assert response.status_code == 200
        assert len(response.json()["chores"]) == 0

    @pytest.mark.parametrize(
        "chore_id,expected_status",
        [
            ("invalid-id", 404),  # Invalid ID
            ("", 405),  # Empty ID - this should be a 405 Method Not Allowed
        ],
    )
    def test_delete_chore_invalid_cases(
        self, client, login_user, chore_id, expected_status
    ):
        token, *_ = login_user
        response = client.delete(
            f"/activities/chores/{chore_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == expected_status


class TestSyncSteps:
    @respx.mock
    def test_sync_steps_success(self, client, login_user):
        token, user_id, email = login_user

        respx.get("https://steps-sync-test.example.com/exec").mock(
            return_value=Response(
                200,
                json=[
                    {"steps": 5000, "date": "2026-05-01"},
                    {"steps": 6000, "date": "2026-05-02"},
                    {"steps": 7000, "date": "2026-05-03"},
                ],
            )
        )

        response = client.post(
            "/activities/steps/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daysSynced"] == 3
        assert data["totalDays"] == 3

        # Verify data is persisted
        response = client.post(
            "/activities/steps/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daysSynced"] == 0
        assert data["totalDays"] == 3

    @respx.mock
    def test_sync_steps_incremental(self, client, login_user):
        token, user_id, email = login_user

        route = respx.get("https://steps-sync-test.example.com/exec")
        route.side_effect = [
            Response(
                200,
                json=[
                    {"steps": 5000, "date": "2026-05-01"},
                    {"steps": 6000, "date": "2026-05-02"},
                ],
            ),
            Response(
                200,
                json=[
                    {"steps": 7000, "date": "2026-05-03"},
                ],
            ),
        ]

        # First sync
        response = client.post(
            "/activities/steps/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daysSynced"] == 2
        assert data["totalDays"] == 2

        # Second sync — only the new day should be synced
        response = client.post(
            "/activities/steps/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daysSynced"] == 1
        assert data["totalDays"] == 3

    @respx.mock
    def test_sync_steps_no_new_data(self, client, login_user):
        token, user_id, email = login_user

        respx.get("https://steps-sync-test.example.com/exec").mock(
            return_value=Response(200, json=[])
        )

        response = client.post(
            "/activities/steps/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daysSynced"] == 0
        assert data["totalDays"] == 0

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_sync_steps_auth_errors(self, client, headers):
        response = client.post("/activities/steps/sync", headers=headers)
        assert response.status_code == 401

    @respx.mock
    def test_sync_steps_with_api_key(self, client, api_key):
        respx.get("https://steps-sync-test.example.com/exec").mock(
            return_value=Response(
                200,
                json=[
                    {"steps": 8000, "date": "2026-05-10"},
                ],
            )
        )

        response = client.post(
            "/activities/steps/sync",
            headers={"X-PK-Api-Key": api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daysSynced"] == 1
        assert data["totalDays"] == 1


class TestGetSteps:
    def test_get_steps_default(self, client, login_user):
        """No params — returns last 30 days with zero-fills."""
        token, user_id, email = login_user

        response = client.get(
            "/activities/steps",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert len(data["entities"]) == 30
        # All items should have steps and date fields
        for item in data["entities"]:
            assert "steps" in item
            assert "date" in item
            assert isinstance(item["steps"], int)
        # Last item should be today
        from datetime import date

        assert data["entities"][-1]["date"] == date.today().isoformat()

    def test_get_steps_with_dates(self, client, login_user):
        """Specific date range — returns that range."""
        token, user_id, email = login_user

        response = client.get(
            "/activities/steps?from=2026-01-01&to=2026-01-05",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 5
        assert data["entities"][0]["date"] == "2026-01-01"
        assert data["entities"][-1]["date"] == "2026-01-05"
        # All items should be zero (no data in DB)
        for item in data["entities"]:
            assert item["steps"] == 0

    def test_get_steps_with_api_key(self, client, api_key):
        """API key auth works."""
        response = client.get(
            "/activities/steps",
            headers={"X-PK-Api-Key": api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert len(data["entities"]) == 30

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_get_steps_auth_errors(self, client, headers):
        response = client.get("/activities/steps", headers=headers)
        assert response.status_code == 401


class TestGetSyncedSteps:
    """Combined tests: sync steps data then verify it via get steps."""

    @respx.mock
    def test_sync_then_get_exact_range(self, client, login_user):
        """Sync several days, then GET an exact range covering them plus gaps."""
        from datetime import date, timedelta

        token, user_id, email = login_user
        today = date.today()

        # Sync 3 specific days: today-20, today-15, today-10
        d1 = (today - timedelta(days=20)).isoformat()
        d2 = (today - timedelta(days=15)).isoformat()
        d3 = (today - timedelta(days=10)).isoformat()
        from_date = (today - timedelta(days=22)).isoformat()
        to_date = (today - timedelta(days=8)).isoformat()

        respx.get("https://steps-sync-test.example.com/exec").mock(
            return_value=Response(
                200,
                json=[
                    {"steps": 5000, "date": d1},
                    {"steps": 8000, "date": d2},
                    {"steps": 3000, "date": d3},
                ],
            )
        )

        sync_resp = client.post(
            "/activities/steps/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sync_resp.status_code == 200
        assert sync_resp.json()["daysSynced"] == 3

        # GET the range from today-22 to today-8 (15 days: covers the 3 synced + gaps)
        response = client.get(
            f"/activities/steps?from={from_date}&to={to_date}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 15

        # Build a dict for easy assertion
        steps_by_date = {e["date"]: e["steps"] for e in data["entities"]}

        # Synced days have their values
        assert steps_by_date[d1] == 5000
        assert steps_by_date[d2] == 8000
        assert steps_by_date[d3] == 3000

        # Gap days are zero-filled (pick a day between d1 and d2)
        gap1 = (today - timedelta(days=19)).isoformat()
        gap2 = (today - timedelta(days=14)).isoformat()
        assert steps_by_date[gap1] == 0
        assert steps_by_date[gap2] == 0

    @respx.mock
    def test_sync_then_get_default_range(self, client, login_user):
        """Sync days within the last 30 days, then GET defaults to verify they appear."""
        from datetime import date, timedelta

        token, user_id, email = login_user
        today = date.today()

        d1 = (today - timedelta(days=5)).isoformat()
        d2 = (today - timedelta(days=3)).isoformat()

        respx.get("https://steps-sync-test.example.com/exec").mock(
            return_value=Response(
                200,
                json=[
                    {"steps": 7000, "date": d1},
                    {"steps": 9000, "date": d2},
                ],
            )
        )

        sync_resp = client.post(
            "/activities/steps/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sync_resp.status_code == 200
        assert sync_resp.json()["daysSynced"] == 2

        # Default GET (last 30 days) should include the synced data
        response = client.get(
            "/activities/steps",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 30
        assert data["entities"][-1]["date"] == today.isoformat()

        steps_by_date = {e["date"]: e["steps"] for e in data["entities"]}
        assert steps_by_date[d1] == 7000
        assert steps_by_date[d2] == 9000

    @respx.mock
    def test_sync_then_get_partial_range(self, client, login_user):
        """Sync several days, then GET a sub-range that only covers some of them."""
        from datetime import date, timedelta

        token, user_id, email = login_user
        today = date.today()

        d_early = (today - timedelta(days=20)).isoformat()
        d_mid = (today - timedelta(days=15)).isoformat()
        d_late = (today - timedelta(days=10)).isoformat()

        respx.get("https://steps-sync-test.example.com/exec").mock(
            return_value=Response(
                200,
                json=[
                    {"steps": 1000, "date": d_early},
                    {"steps": 2000, "date": d_mid},
                    {"steps": 3000, "date": d_late},
                ],
            )
        )

        sync_resp = client.post(
            "/activities/steps/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sync_resp.status_code == 200
        assert sync_resp.json()["daysSynced"] == 3

        # GET only the middle part of the range — only d_mid should appear
        sub_from = (today - timedelta(days=17)).isoformat()
        sub_to = (today - timedelta(days=13)).isoformat()
        response = client.get(
            f"/activities/steps?from={sub_from}&to={sub_to}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 5

        steps_by_date = {e["date"]: e["steps"] for e in data["entities"]}
        assert steps_by_date.get(d_mid) == 2000
        assert d_early not in steps_by_date
        assert d_late not in steps_by_date

    @respx.mock
    def test_get_steps_with_synced_data_uses_api_key(self, client, api_key):
        """API key auth works for the combined sync-then-get flow."""
        from datetime import date, timedelta

        today = date.today()
        d = (today - timedelta(days=7)).isoformat()

        respx.get("https://steps-sync-test.example.com/exec").mock(
            return_value=Response(
                200,
                json=[{"steps": 6000, "date": d}],
            )
        )

        sync_resp = client.post(
            "/activities/steps/sync",
            headers={"X-PK-Api-Key": api_key},
        )
        assert sync_resp.status_code == 200
        assert sync_resp.json()["daysSynced"] == 1

        response = client.get(
            "/activities/steps",
            headers={"X-PK-Api-Key": api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 30

        steps_by_date = {e["date"]: e["steps"] for e in data["entities"]}
        assert steps_by_date[d] == 6000
