import pytest


class TestCreateAndGetPersonalData:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a personal data
        pd_data = {
            "name": "Passport",
            "identifier": "123456789",
            "expiry": "2030-12-31",
        }
        response = client.post(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
            json=pd_data,
        )
        assert response.status_code == 201
        created_pd = response.json()
        assert created_pd["name"] == pd_data["name"]
        assert created_pd["identifier"] == pd_data["identifier"]
        assert created_pd["expiry"] == pd_data["expiry"]

        # Create another personal data (no expiry)
        pd_data2 = {
            "name": "ID Card",
            "identifier": "987654321",
        }
        response = client.post(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
            json=pd_data2,
        )
        assert response.status_code == 201
        created_pd2 = response.json()
        assert created_pd2["name"] == pd_data2["name"]
        assert created_pd2["identifier"] == pd_data2["identifier"]
        assert created_pd2["expiry"] is None

        # Get all personal data
        response = client.get(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        entities = data["entities"]
        assert len(entities) == 2
        assert entities[0]["name"] == pd_data["name"]
        assert entities[0]["identifier"] == pd_data["identifier"]
        assert entities[0]["expiry"] == pd_data["expiry"]
        assert entities[1]["name"] == pd_data2["name"]
        assert entities[1]["identifier"] == pd_data2["identifier"]
        assert entities[1]["expiry"] is None

    def test_create_invalid_token(self, client, login_user):
        # Create with invalid token
        response = client.post(
            "/personal-data/",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "name": "Passport",
                "identifier": "123456789",
                "expiry": "2030-12-31",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_get_personal_data_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        pd_data = {
            "name": "Passport",
            "identifier": "123456789",
        }
        response = client.post(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
            json=pd_data,
        )
        assert response.status_code == 201
        # Get with invalid token
        response = client.get(
            "/personal-data/",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "pd_data,expected_msg",
        [
            # Invalid expiry
            (
                {"name": "Passport", "identifier": "123456789", "expiry": "not-a-date"},
                "String should match pattern",
            ),
            # Name too short
            (
                {"name": "", "identifier": "123456789"},
                "at least 1 character",
            ),
            # Name too long
            (
                {"name": "a" * 101, "identifier": "123456789"},
                "at most 100 characters",
            ),
            # Identifier too short
            (
                {"name": "Passport", "identifier": ""},
                "at least 1 character",
            ),
            # Identifier too long
            (
                {"name": "Passport", "identifier": "a" * 101},
                "at most 100 characters",
            ),
            # Missing required fields
            (
                {"identifier": "123456789"},
                "Field required",
            ),
            (
                {"name": "Passport"},
                "Field required",
            ),
        ],
    )
    def test_create_invalid_data(self, client, login_user, pd_data, expected_msg):
        token, user_id, email = login_user
        response = client.post(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
            json=pd_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestUpdatePersonalData:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        # Create first
        pd_data = {"name": "Passport", "identifier": "123456789"}
        response = client.post(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
            json=pd_data,
        )
        assert response.status_code == 201
        created_pd = response.json()
        pd_id = created_pd["id"]
        # Update
        update_data = {
            "name": "Passport Updated",
            "identifier": "1234567890",
            "expiry": "2040-01-01",
        }
        response = client.put(
            f"/personal-data/{pd_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 200
        updated_pd = response.json()
        assert updated_pd["name"] == update_data["name"]
        assert updated_pd["identifier"] == update_data["identifier"]
        assert updated_pd["expiry"] == update_data["expiry"]
        # Get all to verify
        response = client.get(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert len(entities) == 1
        assert any(
            e["id"] == pd_id and e["name"] == update_data["name"] for e in entities
        )

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        pd_data = {"name": "Passport", "identifier": "123456789"}
        response = client.post(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
            json=pd_data,
        )
        assert response.status_code == 201
        pd_id = response.json()["id"]
        update_data = {"name": "Passport Updated", "identifier": "1234567890"}
        response = client.put(
            f"/personal-data/{pd_id}",
            headers={"Authorization": "Bearer invalid_token"},
            json=update_data,
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_personal_data(self, client, login_user):
        token, user_id, email = login_user
        update_data = {"name": "Passport Updated", "identifier": "1234567890"}
        response = client.put(
            "/personal-data/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: PersonalData" in data["detail"]

    @pytest.mark.parametrize(
        "update_data,expected_msg",
        [
            # Invalid expiry
            (
                {"name": "Passport", "identifier": "123456789", "expiry": "not-a-date"},
                "String should match pattern",
            ),
            # Name too short
            (
                {"name": "", "identifier": "123456789"},
                "at least 1 character",
            ),
            # Name too long
            (
                {"name": "a" * 101, "identifier": "123456789"},
                "at most 100 characters",
            ),
            # Identifier too short
            (
                {"name": "Passport", "identifier": ""},
                "at least 1 character",
            ),
            # Identifier too long
            (
                {"name": "Passport", "identifier": "a" * 101},
                "at most 100 characters",
            ),
            # Missing required fields
            (
                {"identifier": "123456789"},
                "Field required",
            ),
            (
                {"name": "Passport"},
                "Field required",
            ),
        ],
    )
    def test_invalid_data(self, client, login_user, update_data, expected_msg):
        token, user_id, email = login_user
        pd_data = {"name": "Passport", "identifier": "123456789"}
        response = client.post(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
            json=pd_data,
        )
        assert response.status_code == 201
        pd_id = response.json()["id"]
        response = client.put(
            f"/personal-data/{pd_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestDeletePersonalData:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        pd_data = {"name": "To Delete", "identifier": "111111111"}
        response = client.post(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
            json=pd_data,
        )
        assert response.status_code == 201
        pd_id = response.json()["id"]
        response = client.delete(
            f"/personal-data/{pd_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pd_id

        # Verify deletion
        response = client.get(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert len(entities) == 0

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        pd_data = {"name": "To Delete", "identifier": "111111111"}
        response = client.post(
            "/personal-data/",
            headers={"Authorization": f"Bearer {token}"},
            json=pd_data,
        )
        assert response.status_code == 201
        pd_id = response.json()["id"]
        response = client.delete(
            f"/personal-data/{pd_id}",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_personal_data(self, client, login_user):
        token, user_id, email = login_user
        response = client.delete(
            "/personal-data/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: PersonalData" in data["detail"]
