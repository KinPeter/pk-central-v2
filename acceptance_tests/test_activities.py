import re
from datetime import date, timedelta
from pathlib import Path

from httpx import Response

import pytest
import respx


def _replace_gpx_date(gpx_bytes: bytes, new_date: date) -> bytes:
    """Replace all ISO date strings in GPX time tags with *new_date* (time preserved)."""
    content = gpx_bytes.decode("utf-8")
    content = re.sub(
        r"\d{4}-\d{2}-\d{2}(?=T\d{2}:\d{2}:\d{2}Z)",
        new_date.isoformat(),
        content,
    )
    return content.encode("utf-8")


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
            "/activities/config",
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
            "/activities/config",
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
            "/activities/config",
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
        response = client.get("/activities/config", headers=headers)
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
            "/activities/config",
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
            "/activities/config",
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
            "/activities/config",
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
        """No params — returns last 30 days up to yesterday with zero-fills."""
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
        # Last item should be yesterday (using UTC to match API behavior)
        from datetime import datetime, timezone, timedelta

        assert (
            data["entities"][-1]["date"]
            == (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        )

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
        from datetime import datetime, timezone, timedelta

        token, user_id, email = login_user
        today = datetime.now(timezone.utc).date()

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
        from datetime import datetime, timezone, timedelta

        token, user_id, email = login_user
        today = datetime.now(timezone.utc).date()

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

        # Default GET (last 30 days up to yesterday) should include the synced data
        response = client.get(
            "/activities/steps",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 30
        assert data["entities"][-1]["date"] == (today - timedelta(days=1)).isoformat()

        steps_by_date = {e["date"]: e["steps"] for e in data["entities"]}
        assert steps_by_date[d1] == 7000
        assert steps_by_date[d2] == 9000

    @respx.mock
    def test_sync_then_get_partial_range(self, client, login_user):
        """Sync several days, then GET a sub-range that only covers some of them."""
        from datetime import datetime, timezone, timedelta

        token, user_id, email = login_user
        today = datetime.now(timezone.utc).date()

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
        from datetime import datetime, timezone, timedelta

        today = datetime.now(timezone.utc).date()
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


class TestGetActivitiesStats:
    """Stats endpoint tested via uploading real GPX activities"""

    def test_get_stats_with_uploaded_activities(self, client, login_user):
        """Upload walk and ride GPX files, set goals, then verify stats."""
        token, *_ = login_user
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())

        # Walk → last week (Mon-Sun) & this month
        walk_date = this_monday - timedelta(days=7)
        # Ride → last month
        this_month_start = today.replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)
        ride_date = last_month_end.replace(day=15)

        walk_path = Path(__file__).parent / "test_files" / "walk.gpx"
        walk_bytes = _replace_gpx_date(walk_path.read_bytes(), walk_date)
        response = client.post(
            "/activities/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"gpx_file": ("walk.gpx", walk_bytes, "application/gpx+xml")},
            data={"source_id": "stats_walk"},
        )
        assert response.status_code == 201

        ride_path = Path(__file__).parent / "test_files" / "ride.gpx"
        ride_bytes = _replace_gpx_date(ride_path.read_bytes(), ride_date)
        response = client.post(
            "/activities/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"gpx_file": ("ride.gpx", ride_bytes, "application/gpx+xml")},
            data={"source_id": "stats_ride"},
        )
        assert response.status_code == 201

        # Update goals to non-zero values so we can verify them
        body = {
            "walkWeeklyGoal": 30,
            "walkMonthlyGoal": 120,
            "cyclingWeeklyGoal": 60,
            "cyclingMonthlyGoal": 240,
            "stepsWeeklyGoal": 50000,
            "stepsMonthlyGoal": 200000,
        }
        response = client.patch(
            "/activities/goals",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
        )
        assert response.status_code == 200

        # Get stats
        response = client.get(
            "/activities/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Config fields
        assert data["id"] is not None
        assert data["walkWeeklyGoal"] == 30
        assert data["walkMonthlyGoal"] == 120
        assert data["cyclingWeeklyGoal"] == 60
        assert data["cyclingMonthlyGoal"] == 240
        assert data["stepsWeeklyGoal"] == 50000
        assert data["stepsMonthlyGoal"] == 200000

        # Walk stats — walk is 2026-06-01 → last_week and this_month
        assert data["walk"]["thisWeek"] == 0.0
        assert data["walk"]["lastWeek"] > 0.0
        assert data["walk"]["thisMonth"] > 0.0
        assert data["walk"]["lastMonth"] == 0.0

        # Cycling stats — ride is 2026-05-28 → last_month
        assert data["cycling"]["thisWeek"] == 0.0
        assert data["cycling"]["lastWeek"] == 0.0
        assert data["cycling"]["thisMonth"] == 0.0
        assert data["cycling"]["lastMonth"] > 0.0

        # Steps stats are 0 (no steps synced)
        assert data["steps"]["thisWeek"] == 0.0
        assert data["steps"]["lastWeek"] == 0.0
        assert data["steps"]["thisMonth"] == 0.0
        assert data["steps"]["lastMonth"] == 0.0

        # Bike kms should be > 0 because ride upload adds to current_bike_kms
        assert data["currentBikeKms"] > 0.0

        # Chores should be empty
        assert data["chores"] == []

    def test_get_stats_only_walk_uploaded(self, client, login_user):
        """Upload only a walk — cycling and steps remain zero, no bike kms."""
        token, *_ = login_user
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())
        walk_date = this_monday - timedelta(days=7)  # last week & this month

        walk_path = Path(__file__).parent / "test_files" / "walk.gpx"
        walk_bytes = _replace_gpx_date(walk_path.read_bytes(), walk_date)
        response = client.post(
            "/activities/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"gpx_file": ("walk.gpx", walk_bytes, "application/gpx+xml")},
            data={"source_id": "stats_only_walk"},
        )
        assert response.status_code == 201

        response = client.get(
            "/activities/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Walk appears in last_week and this_month
        assert data["walk"]["lastWeek"] > 0.0
        assert data["walk"]["thisMonth"] > 0.0

        # Cycling is all zero
        assert data["cycling"]["thisWeek"] == 0.0
        assert data["cycling"]["lastWeek"] == 0.0
        assert data["cycling"]["thisMonth"] == 0.0
        assert data["cycling"]["lastMonth"] == 0.0

        # Steps are all zero
        assert data["steps"]["thisWeek"] == 0.0
        assert data["steps"]["lastWeek"] == 0.0
        assert data["steps"]["thisMonth"] == 0.0
        assert data["steps"]["lastMonth"] == 0.0

        # No bike kms (no ride uploaded)
        assert data["currentBikeKms"] == 0.0

        # Default goals at 0
        assert data["walkWeeklyGoal"] == 0

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_get_stats_auth_errors(self, client, headers):
        response = client.get("/activities/stats", headers=headers)
        assert response.status_code == 401


class TestUploadActivity:
    """Upload GPX activities and verify the responses."""

    def test_upload_walk_success(self, client, login_user):
        """Upload a walking GPX and verify the parsed activity."""
        token, *_ = login_user
        gpx_path = Path(__file__).parent / "test_files" / "walk.gpx"
        with open(gpx_path, "rb") as f:
            response = client.post(
                "/activities/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "test_upload_walk"},
            )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["id"] is not None

        # Verify by querying activities
        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert len(entities) == 1
        assert entities[0]["type"] == "walk"
        assert entities[0]["sourceId"] == "test_upload_walk"
        assert entities[0]["name"] == "Afternoon Walk"
        assert entities[0]["distance"] > 0
        assert entities[0]["movingTime"] > 0
        assert entities[0]["elapsedTime"] > 0
        assert entities[0]["averageSpeed"] > 0
        assert entities[0]["maxSpeed"] > 0

    def test_upload_ride_success(self, client, login_user):
        """Upload a cycling GPX and verify the parsed activity."""
        token, *_ = login_user
        gpx_path = Path(__file__).parent / "test_files" / "ride.gpx"
        with open(gpx_path, "rb") as f:
            response = client.post(
                "/activities/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"gpx_file": ("ride.gpx", f, "application/gpx+xml")},
                data={"source_id": "test_upload_ride"},
            )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert len(entities) == 1
        assert entities[0]["type"] == "ride"
        assert entities[0]["sourceId"] == "test_upload_ride"
        assert entities[0]["name"] == "Afternoon Ride"
        assert entities[0]["distance"] > 0

    def test_upload_boating_success(self, client, login_user):
        """Upload a boating GPX and verify the parsed activity."""
        token, *_ = login_user
        gpx_path = Path(__file__).parent / "test_files" / "boating.gpx"
        with open(gpx_path, "rb") as f:
            response = client.post(
                "/activities/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"gpx_file": ("boating.gpx", f, "application/gpx+xml")},
                data={"source_id": "test_upload_boating"},
            )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert len(entities) == 1
        assert entities[0]["type"] == "boating"
        assert entities[0]["sourceId"] == "test_upload_boating"
        assert entities[0]["name"] == "Danube boating"
        assert entities[0]["distance"] > 0

    def test_upload_duplicate_source_id(self, client, login_user):
        """Uploading the same source_id twice returns 409 Conflict."""
        token, *_ = login_user
        gpx_path = Path(__file__).parent / "test_files" / "walk.gpx"

        with open(gpx_path, "rb") as f:
            response = client.post(
                "/activities/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "test_duplicate"},
            )
        assert response.status_code == 201

        with open(gpx_path, "rb") as f:
            response = client.post(
                "/activities/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "test_duplicate"},
            )
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "already synced" in data["detail"].lower()

    def test_upload_invalid_file(self, client, login_user):
        """Uploading a non-GPX file returns 422."""
        token, *_ = login_user
        response = client.post(
            "/activities/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "gpx_file": ("not_a_gpx.txt", b"this is not a gpx file", "text/plain")
            },
            data={"source_id": "test_invalid"},
        )
        assert response.status_code == 422

    def test_upload_empty_source_id(self, client, login_user):
        """Uploading with an empty source_id returns 422."""
        token, *_ = login_user
        gpx_path = Path(__file__).parent / "test_files" / "walk.gpx"
        with open(gpx_path, "rb") as f:
            response = client.post(
                "/activities/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": ""},
            )
        assert response.status_code == 422

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_upload_auth_errors(self, client, headers):
        """Upload with invalid auth returns 401."""
        gpx_path = Path(__file__).parent / "test_files" / "walk.gpx"
        with open(gpx_path, "rb") as f:
            response = client.post(
                "/activities/upload",
                headers=headers,
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "test_auth_err"},
            )
        assert response.status_code == 401

    def test_upload_with_api_key(self, client, api_key):
        """Upload using API key auth succeeds."""
        gpx_path = Path(__file__).parent / "test_files" / "walk.gpx"
        with open(gpx_path, "rb") as f:
            response = client.post(
                "/activities/upload",
                headers={"X-PK-Api-Key": api_key},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "test_api_key_upload"},
            )
        assert response.status_code == 201
        assert "id" in response.json()


class TestVerifyActivitySync:
    """Verify sync status of uploaded activity source IDs."""

    def test_verify_sync_none_uploaded(self, client, login_user):
        """No activities uploaded — all requested IDs are unsynced."""
        token, *_ = login_user
        response = client.post(
            "/activities/verify-sync",
            headers={"Authorization": f"Bearer {token}"},
            json={"activityIds": ["strava_1", "strava_2", "strava_3"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data["unsynced"]) == {"strava_1", "strava_2", "strava_3"}

    def test_verify_sync_all_uploaded(self, client, login_user):
        """After uploading all IDs, verify-sync returns empty unsynced."""
        token, *_ = login_user
        gpx_path = Path(__file__).parent / "test_files" / "walk.gpx"

        with open(gpx_path, "rb") as f:
            client.post(
                "/activities/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "sync_all_1"},
            )
        with open(gpx_path, "rb") as f:
            client.post(
                "/activities/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "sync_all_2"},
            )

        response = client.post(
            "/activities/verify-sync",
            headers={"Authorization": f"Bearer {token}"},
            json={"activityIds": ["sync_all_1", "sync_all_2"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unsynced"] == []

    def test_verify_sync_mixed(self, client, login_user):
        """Some IDs uploaded, some not — only missing ones are unsynced."""
        token, *_ = login_user
        gpx_path = Path(__file__).parent / "test_files" / "walk.gpx"
        with open(gpx_path, "rb") as f:
            client.post(
                "/activities/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "synced_id"},
            )

        response = client.post(
            "/activities/verify-sync",
            headers={"Authorization": f"Bearer {token}"},
            json={"activityIds": ["synced_id", "unsynced_1", "unsynced_2"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data["unsynced"]) == {"unsynced_1", "unsynced_2"}

    def test_verify_sync_empty_request(self, client, login_user):
        """Empty activity IDs list — returns empty unsynced list."""
        token, *_ = login_user
        response = client.post(
            "/activities/verify-sync",
            headers={"Authorization": f"Bearer {token}"},
            json={"activityIds": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unsynced"] == []

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_verify_sync_auth_errors(self, client, headers):
        response = client.post(
            "/activities/verify-sync",
            headers=headers,
            json={"activityIds": ["some_id"]},
        )
        assert response.status_code == 401

    def test_verify_sync_with_api_key(self, client, api_key):
        """Verify sync using API key auth."""
        gpx_path = Path(__file__).parent / "test_files" / "walk.gpx"
        with open(gpx_path, "rb") as f:
            client.post(
                "/activities/upload",
                headers={"X-PK-Api-Key": api_key},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "api_key_synced"},
            )

        response = client.post(
            "/activities/verify-sync",
            headers={"X-PK-Api-Key": api_key},
            json={"activityIds": ["api_key_synced", "api_key_unsynced"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unsynced"] == ["api_key_unsynced"]


class TestQueryActivities:
    """Query activities with various filters after uploading GPX files."""

    def _upload_all_three(self, client, token):
        """Helper: upload all 3 GPX test files."""
        for filename, sid in [
            ("walk.gpx", "q_walk"),
            ("ride.gpx", "q_ride"),
            ("boating.gpx", "q_boat"),
        ]:
            gpx_path = Path(__file__).parent / "test_files" / filename
            with open(gpx_path, "rb") as f:
                client.post(
                    "/activities/upload",
                    headers={"Authorization": f"Bearer {token}"},
                    files={"gpx_file": (filename, f, "application/gpx+xml")},
                    data={"source_id": sid},
                )

    def test_query_all(self, client, login_user):
        """Query without filters returns all uploaded activities."""
        token, *_ = login_user
        self._upload_all_three(client, token)

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert len(data["entities"]) == 3

        types = {e["type"] for e in data["entities"]}
        assert types == {"walk", "ride", "boating"}

    def test_query_by_type_walk(self, client, login_user):
        """Filter by walk type returns only the walk activity."""
        token, *_ = login_user
        self._upload_all_three(client, token)

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"types": ["walk"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["type"] == "walk"

    def test_query_by_type_ride(self, client, login_user):
        """Filter by ride type returns only the ride activity."""
        token, *_ = login_user
        self._upload_all_three(client, token)

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"types": ["ride"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["type"] == "ride"

    def test_query_by_type_boating(self, client, login_user):
        """Filter by boating type returns only the boating activity."""
        token, *_ = login_user
        self._upload_all_three(client, token)

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"types": ["boating"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["type"] == "boating"

    def test_query_by_multiple_types(self, client, login_user):
        """Filter by multiple types returns matching activities."""
        token, *_ = login_user
        self._upload_all_three(client, token)

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"types": ["walk", "ride"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 2
        types = {e["type"] for e in data["entities"]}
        assert types == {"walk", "ride"}

    def test_query_by_date_range(self, client, login_user):
        """Filter by date range — only walk (2026-06-01) falls in early June."""
        token, *_ = login_user
        self._upload_all_three(client, token)

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"fromDate": "2026-06-01", "toDate": "2026-06-07"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["type"] == "walk"

    def test_query_empty_result(self, client, login_user):
        """Query with a non-matching filter returns empty list."""
        token, *_ = login_user
        self._upload_all_three(client, token)

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"types": ["walk"], "fromDate": "2099-01-01", "toDate": "2099-12-31"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["entities"] == []

    def test_query_no_activities_uploaded(self, client, login_user):
        """No activities uploaded at all — returns empty list."""
        token, *_ = login_user

        response = client.post(
            "/activities/query",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["entities"] == []

    @pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
    def test_query_auth_errors(self, client, headers):
        """Query with invalid auth returns 401."""
        response = client.post(
            "/activities/query",
            headers=headers,
            json={},
        )
        assert response.status_code == 401

    def test_query_with_api_key(self, client, api_key):
        """Query using API key auth."""
        gpx_path = Path(__file__).parent / "test_files" / "walk.gpx"
        with open(gpx_path, "rb") as f:
            client.post(
                "/activities/upload",
                headers={"X-PK-Api-Key": api_key},
                files={"gpx_file": ("walk.gpx", f, "application/gpx+xml")},
                data={"source_id": "api_key_query"},
            )

        response = client.post(
            "/activities/query",
            headers={"X-PK-Api-Key": api_key},
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert data["entities"][0]["sourceId"] == "api_key_query"
