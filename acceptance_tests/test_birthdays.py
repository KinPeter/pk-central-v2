import pytest


class TestCreateAndGetBirthdays:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a birthday
        bday_data = {
            "name": "Alice",
            "date": "1/12",
        }
        response = client.post(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
            json=bday_data,
        )
        assert response.status_code == 201
        created_bday = response.json()
        assert created_bday["name"] == bday_data["name"]
        assert created_bday["date"] == bday_data["date"]

        # Create another birthday
        bday_data2 = {
            "name": "Bob",
            "date": "11/30",
        }
        response = client.post(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
            json=bday_data2,
        )
        assert response.status_code == 201
        created_bday2 = response.json()
        assert created_bday2["name"] == bday_data2["name"]
        assert created_bday2["date"] == bday_data2["date"]

        # Get all birthdays
        response = client.get(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        entities = data["entities"]
        assert len(entities) == 2
        assert entities[0]["name"] == bday_data["name"]
        assert entities[0]["date"] == bday_data["date"]
        assert entities[1]["name"] == bday_data2["name"]
        assert entities[1]["date"] == bday_data2["date"]

    def test_create_invalid_token(self, client, login_user):
        # Create with invalid token
        response = client.post(
            "/birthdays/",
            headers={"Authorization": "Bearer invalid_token"},
            json={"name": "Alice", "date": "1/12"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_get_birthdays_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        bday_data = {"name": "Alice", "date": "1/12"}
        response = client.post(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
            json=bday_data,
        )
        assert response.status_code == 201
        # Get with invalid token
        response = client.get(
            "/birthdays/",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "bday_data,expected_msg",
        [
            # Invalid date
            ({"name": "Alice", "date": "13/12"}, "String should match pattern"),
            ({"name": "Alice", "date": "2/32"}, "String should match pattern"),
            ({"name": "Alice", "date": "notadate"}, "String should match pattern"),
            # Name too short
            ({"name": "", "date": "1/12"}, "at least 1 character"),
            # Name too long
            ({"name": "a" * 101, "date": "1/12"}, "at most 100 characters"),
            # Missing required fields
            ({"date": "1/12"}, "Field required"),
            ({"name": "Alice"}, "Field required"),
        ],
    )
    def test_create_invalid_data(self, client, login_user, bday_data, expected_msg):
        token, user_id, email = login_user
        response = client.post(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
            json=bday_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestUpdateBirthday:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        # Create first
        bday_data = {"name": "Alice", "date": "1/12"}
        response = client.post(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
            json=bday_data,
        )
        assert response.status_code == 201
        created_bday = response.json()
        bday_id = created_bday["id"]
        # Update
        update_data = {"name": "Alice Updated", "date": "2/28"}
        response = client.put(
            f"/birthdays/{bday_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 200
        updated_bday = response.json()
        assert updated_bday["name"] == update_data["name"]
        assert updated_bday["date"] == update_data["date"]
        # Get all to verify
        response = client.get(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert any(
            e["id"] == bday_id and e["name"] == update_data["name"] for e in entities
        )

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        bday_data = {"name": "Alice", "date": "1/12"}
        response = client.post(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
            json=bday_data,
        )
        assert response.status_code == 201
        bday_id = response.json()["id"]
        update_data = {"name": "Alice Updated", "date": "2/28"}
        response = client.put(
            f"/birthdays/{bday_id}",
            headers={"Authorization": "Bearer invalid_token"},
            json=update_data,
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_birthday(self, client, login_user):
        token, user_id, email = login_user
        update_data = {"name": "Alice Updated", "date": "2/28"}
        response = client.put(
            "/birthdays/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Birthday" in data["detail"]

    @pytest.mark.parametrize(
        "update_data,expected_msg",
        [
            # Invalid date
            ({"name": "Alice", "date": "13/12"}, "String should match pattern"),
            ({"name": "Alice", "date": "2/32"}, "String should match pattern"),
            ({"name": "Alice", "date": "notadate"}, "String should match pattern"),
            # Name too short
            ({"name": "", "date": "1/12"}, "at least 1 character"),
            # Name too long
            ({"name": "a" * 101, "date": "1/12"}, "at most 100 characters"),
            # Missing required fields
            ({"date": "1/12"}, "Field required"),
            ({"name": "Alice"}, "Field required"),
        ],
    )
    def test_invalid_data(self, client, login_user, update_data, expected_msg):
        token, user_id, email = login_user
        bday_data = {"name": "Alice", "date": "1/12"}
        response = client.post(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
            json=bday_data,
        )
        assert response.status_code == 201
        bday_id = response.json()["id"]
        response = client.put(
            f"/birthdays/{bday_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestDeleteBirthday:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        bday_data = {"name": "To Delete", "date": "3/15"}
        response = client.post(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
            json=bday_data,
        )
        assert response.status_code == 201
        bday_id = response.json()["id"]
        response = client.delete(
            f"/birthdays/{bday_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bday_id

        # Verify deletion
        response = client.get(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert all(e["id"] != bday_id for e in entities)

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        bday_data = {"name": "To Delete", "date": "3/15"}
        response = client.post(
            "/birthdays/",
            headers={"Authorization": f"Bearer {token}"},
            json=bday_data,
        )
        assert response.status_code == 201
        bday_id = response.json()["id"]
        response = client.delete(
            f"/birthdays/{bday_id}",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_birthday(self, client, login_user):
        token, user_id, email = login_user
        response = client.delete(
            "/birthdays/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Birthday" in data["detail"]
