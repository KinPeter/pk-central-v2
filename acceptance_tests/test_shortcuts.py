import pytest


class TestCreateAndGetShortcuts:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a shortcut
        shortcut_data = {
            "name": "Google",
            "url": "https://google.com/",
            "iconUrl": "https://google.com/icon.png",
            "category": "GOOGLE",
            "priority": 1,
        }
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
            json=shortcut_data,
        )
        assert response.status_code == 201
        created_shortcut = response.json()
        assert created_shortcut["name"] == shortcut_data["name"]
        assert created_shortcut["url"] == shortcut_data["url"]
        assert created_shortcut["iconUrl"] == shortcut_data["iconUrl"]
        assert created_shortcut["category"] == shortcut_data["category"]
        assert created_shortcut["priority"] == shortcut_data["priority"]

        # Create another shortcut
        shortcut_data2 = {
            "name": "GitHub",
            "url": "https://github.com/",
            "iconUrl": "https://github.com/icon.png",
            "category": "CODING",
            "priority": 2,
        }
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
            json=shortcut_data2,
        )
        assert response.status_code == 201
        created_shortcut2 = response.json()
        assert created_shortcut2["name"] == shortcut_data2["name"]
        assert created_shortcut2["url"] == shortcut_data2["url"]
        assert created_shortcut2["iconUrl"] == shortcut_data2["iconUrl"]
        assert created_shortcut2["category"] == shortcut_data2["category"]
        assert created_shortcut2["priority"] == shortcut_data2["priority"]

        # Get all shortcuts
        response = client.get(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        shortcuts = data["entities"]
        assert len(shortcuts) == 2
        assert shortcuts[0]["name"] == shortcut_data["name"]
        assert shortcuts[0]["url"] == shortcut_data["url"]
        assert shortcuts[0]["iconUrl"] == shortcut_data["iconUrl"]
        assert shortcuts[0]["category"] == shortcut_data["category"]
        assert shortcuts[0]["priority"] == shortcut_data["priority"]
        assert shortcuts[1]["name"] == shortcut_data2["name"]
        assert shortcuts[1]["url"] == shortcut_data2["url"]
        assert shortcuts[1]["iconUrl"] == shortcut_data2["iconUrl"]
        assert shortcuts[1]["category"] == shortcut_data2["category"]
        assert shortcuts[1]["priority"] == shortcut_data2["priority"]

    def test_create_invalid_token(self, client, login_user):
        # Create a shortcut with an invalid token
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "name": "Google",
                "url": "https://google.com/",
                "iconUrl": "https://google.com/icon.png",
                "category": "GOOGLE",
                "priority": 1,
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_get_shortcuts_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        # Create a shortcut first
        shortcut_data = {
            "name": "Google",
            "url": "https://google.com/",
            "iconUrl": "https://google.com/icon.png",
            "category": "GOOGLE",
            "priority": 1,
        }
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
            json=shortcut_data,
        )
        assert response.status_code == 201
        # Get shortcuts with an invalid token
        response = client.get(
            "/shortcuts/",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "shortcut_data,expected_msg",
        [
            (
                {
                    "name": "Google",
                    "url": "not-a-url",
                    "iconUrl": "https://google.com/icon.png",
                    "category": "GOOGLE",
                    "priority": 1,
                },
                "valid URL",
            ),
            (
                {
                    "name": "",
                    "url": "https://google.com/",
                    "iconUrl": "https://google.com/icon.png",
                    "category": "GOOGLE",
                    "priority": 1,
                },
                "at least 1 character",
            ),
            (
                {
                    "name": "a" * 101,  # Exceeding max length
                    "url": "https://google.com/",
                    "iconUrl": "https://google.com/icon.png",
                    "category": "GOOGLE",
                    "priority": 1,
                },
                "at most 100 characters",
            ),
            (
                {
                    "name": "Google",
                    "url": "https://google.com/",
                    "iconUrl": "not-a-url",
                    "category": "GOOGLE",
                    "priority": 1,
                },
                "valid URL",
            ),
            (
                {
                    "name": "Google",
                    "url": "https://google.com/",
                    "iconUrl": "https://google.com/icon.png",
                    "category": "INVALID",
                    "priority": 1,
                },
                "Input should be",
            ),
            (
                {
                    "name": "Google",
                    "url": "https://google.com/",
                    "iconUrl": "https://google.com/icon.png",
                    "category": "GOOGLE",
                    "priority": 0,
                },
                "greater than or equal to 1",
            ),
            # Missing required fields
            (
                {
                    # missing 'name'
                    "url": "https://google.com/",
                    "iconUrl": "https://google.com/icon.png",
                    "category": "GOOGLE",
                    "priority": 1,
                },
                "Field required",
            ),
            (
                {
                    "name": "Google",
                    # missing 'url'
                    "iconUrl": "https://google.com/icon.png",
                    "category": "GOOGLE",
                    "priority": 1,
                },
                "Field required",
            ),
            (
                {
                    "name": "Google",
                    "url": "https://google.com/",
                    # missing 'iconUrl'
                    "category": "GOOGLE",
                    "priority": 1,
                },
                "Field required",
            ),
            (
                {
                    "name": "Google",
                    "url": "https://google.com/",
                    "iconUrl": "https://google.com/icon.png",
                    # missing 'category'
                    "priority": 1,
                },
                "Field required",
            ),
            (
                {
                    "name": "Google",
                    "url": "https://google.com/",
                    "iconUrl": "https://google.com/icon.png",
                    "category": "GOOGLE",
                    # missing 'priority'
                },
                "Field required",
            ),
        ],
    )
    def test_create_invalid_data(self, client, login_user, shortcut_data, expected_msg):
        token, user_id, email = login_user
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
            json=shortcut_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestUpdateShortcut:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        # Create a shortcut first
        shortcut_data = {
            "name": "Google",
            "url": "https://google.com/",
            "iconUrl": "https://google.com/icon.png",
            "category": "GOOGLE",
            "priority": 1,
        }
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
            json=shortcut_data,
        )
        assert response.status_code == 201
        created_shortcut = response.json()
        shortcut_id = created_shortcut["id"]
        # Update the shortcut
        update_data = {
            "name": "Google Updated",
            "url": "https://google.com/updated/",
            "iconUrl": "https://google.com/icon-updated.png",
            "category": "GOOGLE",
            "priority": 2,
        }
        response = client.put(
            f"/shortcuts/{shortcut_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 200
        updated_shortcut = response.json()
        assert updated_shortcut["name"] == update_data["name"]
        assert updated_shortcut["url"] == update_data["url"]
        assert updated_shortcut["iconUrl"] == update_data["iconUrl"]
        assert updated_shortcut["category"] == update_data["category"]
        assert updated_shortcut["priority"] == update_data["priority"]
        # Get all shortcuts to verify update
        response = client.get(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        shortcuts = data["entities"]
        assert any(
            s["id"] == shortcut_id and s["name"] == update_data["name"]
            for s in shortcuts
        )

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        # Create a shortcut first
        shortcut_data = {
            "name": "Google",
            "url": "https://google.com/",
            "iconUrl": "https://google.com/icon.png",
            "category": "GOOGLE",
            "priority": 1,
        }
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
            json=shortcut_data,
        )
        assert response.status_code == 201
        created_shortcut = response.json()
        shortcut_id = created_shortcut["id"]
        # Attempt to update with an invalid token
        update_data = {
            "name": "Google Updated",
            "url": "https://google.com/updated/",
            "iconUrl": "https://google.com/icon-updated.png",
            "category": "GOOGLE",
            "priority": 2,
        }
        response = client.put(
            f"/shortcuts/{shortcut_id}",
            headers={"Authorization": "Bearer invalid_token"},
            json=update_data,
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_shortcut(self, client, login_user):
        token, user_id, email = login_user
        # Attempt to update a shortcut that does not exist
        update_data = {
            "name": "Google Updated",
            "url": "https://google.com/updated/",
            "iconUrl": "https://google.com/icon-updated.png",
            "category": "GOOGLE",
            "priority": 2,
        }
        response = client.put(
            "/shortcuts/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Shortcut" in data["detail"]

    @pytest.mark.parametrize(
        "update_data,expected_msg",
        [
            (
                {
                    "name": "Google Updated",
                    "url": "not-a-url",
                    "iconUrl": "https://google.com/icon-updated.png",
                    "category": "GOOGLE",
                    "priority": 2,
                },
                "valid URL",
            ),
            (
                {
                    "name": "",
                    "url": "https://google.com/updated/",
                    "iconUrl": "https://google.com/icon-updated.png",
                    "category": "GOOGLE",
                    "priority": 2,
                },
                "at least 1 character",
            ),
            (
                {
                    "name": "a" * 101,  # Exceeding max length
                    "url": "https://google.com/updated/",
                    "iconUrl": "https://google.com/icon-updated.png",
                    "category": "GOOGLE",
                    "priority": 2,
                },
                "at most 100 characters",
            ),
            (
                {
                    "name": "Google Updated",
                    "url": "https://google.com/updated/",
                    "iconUrl": "not-a-url",
                    "category": "GOOGLE",
                    "priority": 2,
                },
                "valid URL",
            ),
            (
                {
                    "name": "Google Updated",
                    "url": "https://google.com/updated/",
                    "iconUrl": "https://google.com/icon-updated.png",
                    "category": "INVALID",
                    "priority": 2,
                },
                "Input should be ",
            ),
            (
                {
                    "name": "Google Updated",
                    "url": "https://google.com/updated/",
                    "iconUrl": "https://google.com/icon-updated.png",
                    "category": "GOOGLE",
                    "priority": 0,
                },
                "greater than or equal to 1",
            ),
            # Missing required fields
            (
                {
                    # missing 'name'
                    "url": "https://google.com/updated/",
                    "iconUrl": "https://google.com/icon-updated.png",
                    "category": "GOOGLE",
                    "priority": 2,
                },
                "Field required",
            ),
            (
                {
                    "name": "Google Updated",
                    # missing 'url'
                    "iconUrl": "https://google.com/icon-updated.png",
                    "category": "GOOGLE",
                    "priority": 2,
                },
                "Field required",
            ),
            (
                {
                    "name": "Google Updated",
                    "url": "https://google.com/updated/",
                    # missing 'iconUrl'
                    "category": "GOOGLE",
                    "priority": 2,
                },
                "Field required",
            ),
            (
                {
                    "name": "Google Updated",
                    "url": "https://google.com/updated/",
                    "iconUrl": "https://google.com/icon-updated.png",
                    # missing 'category'
                    "priority": 2,
                },
                "Field required",
            ),
            (
                {
                    "name": "Google Updated",
                    "url": "https://google.com/updated/",
                    "iconUrl": "https://google.com/icon-updated.png",
                    "category": "GOOGLE",
                    # missing 'priority'
                },
                "Field required",
            ),
        ],
    )
    def test_invalid_data(self, client, login_user, update_data, expected_msg):
        token, user_id, email = login_user
        # Create a shortcut first
        shortcut_data = {
            "name": "Google",
            "url": "https://google.com/",
            "iconUrl": "https://google.com/icon.png",
            "category": "GOOGLE",
            "priority": 1,
        }
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
            json=shortcut_data,
        )
        assert response.status_code == 201
        created_shortcut = response.json()
        shortcut_id = created_shortcut["id"]
        # Attempt to update with invalid data
        response = client.put(
            f"/shortcuts/{shortcut_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestDeleteShortcut:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        # Create a shortcut first
        shortcut_data = {
            "name": "To Delete",
            "url": "https://delete.com/",
            "iconUrl": "https://delete.com/icon.png",
            "category": "OTHERS",
            "priority": 3,
        }
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
            json=shortcut_data,
        )
        assert response.status_code == 201
        created_shortcut = response.json()
        shortcut_id = created_shortcut["id"]
        # Delete the shortcut
        response = client.delete(
            f"/shortcuts/{shortcut_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == shortcut_id

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        # Create a shortcut first
        shortcut_data = {
            "name": "To Delete",
            "url": "https://delete.com/",
            "iconUrl": "https://delete.com/icon.png",
            "category": "OTHERS",
            "priority": 3,
        }
        response = client.post(
            "/shortcuts/",
            headers={"Authorization": f"Bearer {token}"},
            json=shortcut_data,
        )
        assert response.status_code == 201
        created_shortcut = response.json()
        shortcut_id = created_shortcut["id"]
        # Attempt to delete with an invalid token
        response = client.delete(
            f"/shortcuts/{shortcut_id}",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_shortcut(self, client, login_user):
        token, user_id, email = login_user
        # Attempt to delete a shortcut that does not exist
        response = client.delete(
            "/shortcuts/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Shortcut" in data["detail"]
