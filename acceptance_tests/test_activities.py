import pytest


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

        # Updating goals
        body = {
            "walkWeeklyGoal": 1000,
            "walkMonthlyGoal": 4000,
            "cyclingWeeklyGoal": 200,
            "cyclingMonthlyGoal": 800,
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

    def test_update_goals_unauthorized(self, client):
        # No token provided
        body = {
            "walkWeeklyGoal": 1000,
            "walkMonthlyGoal": 4000,
            "cyclingWeeklyGoal": 200,
            "cyclingMonthlyGoal": 800,
        }
        response = client.patch("/activities/goals", json=body)
        assert response.status_code in (401, 403)


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

    def test_add_chore_unauthorized(self, client):
        # No token provided
        body = {
            "name": "Test Chore",
            "kmInterval": 30,
            "lastKm": 0.0,
        }
        response = client.post("/activities/chores", json=body)
        assert response.status_code in (401, 403)


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
