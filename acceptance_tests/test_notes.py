import pytest
import re


class TestCreateAndGetNotes:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a note
        note_data = {
            "text": "Test note",
            "links": [
                {"name": "Google", "url": "https://google.com/"},
                {"name": "GitHub", "url": "https://github.com/"},
                {"name": "Python", "url": "https://python.org/"},
            ],
            "archived": True,
            "pinned": True,
        }
        response = client.post(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json=note_data,
        )
        assert response.status_code == 201
        created_note = response.json()
        assert created_note["text"] == note_data["text"]
        assert len(created_note["links"]) == len(note_data["links"])
        assert created_note["archived"] is True
        assert created_note["pinned"] is True
        assert "createdAt" in created_note
        # Should be ISO format with 'Z' or '+00:00'
        assert re.match(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+(\+00:00|Z)$",
            created_note["createdAt"],
        ) or created_note["createdAt"].endswith("Z")

        # Create another note
        note_data_minimal = {
            "text": None,
            "links": [{"name": "Google", "url": "https://google.com/"}],
            "archived": False,
            "pinned": False,
        }
        response = client.post(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json=note_data_minimal,
        )
        assert response.status_code == 201
        created_note_minimal = response.json()
        assert created_note_minimal["text"] is None
        assert len(created_note_minimal["links"]) == 1
        assert created_note_minimal["archived"] is False
        assert created_note_minimal["pinned"] is False
        assert "createdAt" in created_note_minimal
        # Should be ISO format with 'Z' or '+00:00'
        assert re.match(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+(\+00:00|Z)$",
            created_note_minimal["createdAt"],
        ) or created_note_minimal["createdAt"].endswith("Z")

        # Get all notes
        response = client.get(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        notes = data["entities"]
        assert len(notes) == 2
        assert notes[0]["text"] == note_data["text"]
        assert notes[0]["archived"] is True
        assert notes[0]["pinned"] is True
        assert len(notes[0]["links"]) == len(note_data["links"])
        assert notes[0]["links"][0]["name"] == "Google"
        assert notes[0]["links"][0]["url"] == "https://google.com/"
        assert notes[0]["links"][1]["name"] == "GitHub"
        assert notes[0]["links"][1]["url"] == "https://github.com/"
        assert notes[0]["links"][2]["name"] == "Python"
        assert notes[0]["links"][2]["url"] == "https://python.org/"
        assert notes[1]["text"] is None
        assert len(notes[1]["links"]) == 1
        assert notes[1]["archived"] is False
        assert notes[1]["pinned"] is False

    def test_create_invalid_token(self, client, login_user):
        token, user_id, email = login_user

        # Create a note with an invalid token
        response = client.post(
            "/notes/",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "text": "Test note",
                "links": [],
                "archived": False,
                "pinned": False,
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_get_notes_invalid_token(self, client, login_user):
        token, user_id, email = login_user

        # Create a note first
        note_data = {
            "text": "Test note",
            "links": [],
            "archived": False,
            "pinned": False,
        }
        response = client.post(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json=note_data,
        )
        assert response.status_code == 201

        # Get notes with an invalid token
        response = client.get(
            "/notes/",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "note_data,expected_msg",
        [
            (
                {
                    "text": "Test note",
                    "links": [{"name": "Google", "url": "not-a-url"}],
                    "archived": False,
                    "pinned": False,
                },
                "valid URL",
            ),
            (
                {
                    "text": "Test note",
                    "links": [{"name": "", "url": "https://google.com"}],
                    "archived": False,
                    "pinned": False,
                },
                "at least 1 character",
            ),
            (
                {
                    "text": "a" * 1001,  # Exceeding max length
                    "links": [],
                    "archived": False,
                    "pinned": False,
                },
                "at most 1000 characters",
            ),
            (
                {
                    "text": "Test note",
                    "links": [],
                    "archived": False,
                    "pinned": "not-a-boolean",  # Invalid type
                },
                "a valid boolean",
            ),
        ],
    )
    def test_create_invalid_data(self, client, login_user, note_data, expected_msg):
        token, user_id, email = login_user

        # Attempt to create a note with invalid data
        response = client.post(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json=note_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestUpdateNote:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a note first
        note_data = {
            "text": "Initial note",
            "links": [],
            "archived": False,
            "pinned": False,
        }
        response = client.post(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json=note_data,
        )
        assert response.status_code == 201
        created_note = response.json()
        note_id = created_note["id"]

        # Update the note
        update_data = {
            "text": "Updated note",
            "links": [{"name": "Updated Link", "url": "https://updated.com"}],
            "archived": True,
            "pinned": True,
        }
        response = client.put(
            f"/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 200
        updated_note = response.json()
        assert updated_note["text"] == update_data["text"]
        assert len(updated_note["links"]) == 1
        assert updated_note["links"][0]["name"] == "Updated Link"
        assert updated_note["links"][0]["url"] == "https://updated.com/"
        assert updated_note["archived"] is True
        assert updated_note["pinned"] is True

        # Get all notes to verify update
        response = client.get(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        notes = data["entities"]
        assert len(notes) == 1
        assert notes[0]["id"] == note_id
        assert notes[0]["text"] == update_data["text"]
        assert notes[0]["archived"] is True
        assert notes[0]["pinned"] is True
        assert len(notes[0]["links"]) == 1
        assert notes[0]["links"][0]["name"] == "Updated Link"
        assert notes[0]["links"][0]["url"] == "https://updated.com/"

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user

        # Create a note first
        note_data = {
            "text": "Initial note",
            "links": [],
            "archived": False,
            "pinned": False,
        }
        response = client.post(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json=note_data,
        )
        assert response.status_code == 201
        created_note = response.json()
        note_id = created_note["id"]

        # Attempt to update with an invalid token
        update_data = {
            "text": "Updated note",
            "links": [],
            "archived": False,
            "pinned": False,
        }
        response = client.put(
            f"/notes/{note_id}",
            headers={"Authorization": "Bearer invalid_token"},
            json=update_data,
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_note(self, client, login_user):
        token, user_id, email = login_user

        # Attempt to update a note that does not exist
        update_data = {
            "text": "Updated note",
            "links": [],
            "archived": False,
            "pinned": False,
        }
        response = client.put(
            "/notes/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Note" in data["detail"]

    @pytest.mark.parametrize(
        "update_data,expected_msg",
        [
            (
                {
                    "text": "Updated note",
                    "links": [{"name": "Invalid Link", "url": "not-a-url"}],
                    "archived": False,
                    "pinned": False,
                },
                "valid URL",
            ),
            (
                {
                    "text": "",
                    "links": [{"name": "", "url": "https://google.com"}],
                    "archived": False,
                    "pinned": False,
                },
                "at least 1 character",
            ),
            (
                {
                    "text": "a" * 1001,  # Exceeding max length
                    "links": [],
                    "archived": False,
                    "pinned": False,
                },
                "at most 1000 characters",
            ),
            (
                {
                    "text": "Updated note",
                    "links": [],
                    "archived": False,
                    "pinned": "not-a-boolean",  # Invalid type
                },
                "a valid boolean",
            ),
        ],
    )
    def test_invalid_data(self, client, login_user, update_data, expected_msg):
        token, user_id, email = login_user

        # Create a note first
        note_data = {
            "text": "Initial note",
            "links": [],
            "archived": False,
            "pinned": False,
        }
        response = client.post(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json=note_data,
        )
        assert response.status_code == 201
        created_note = response.json()
        note_id = created_note["id"]

        # Attempt to update the note with invalid data
        response = client.put(
            f"/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestDeleteNote:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a note first
        note_data = {
            "text": "Note to delete",
            "links": [],
            "archived": False,
            "pinned": False,
        }
        response = client.post(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json=note_data,
        )
        assert response.status_code == 201
        created_note = response.json()
        note_id = created_note["id"]

        # Delete the note
        response = client.delete(
            f"/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == note_id

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user

        # Create a note first
        note_data = {
            "text": "Note to delete",
            "links": [],
            "archived": False,
            "pinned": False,
        }
        response = client.post(
            "/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json=note_data,
        )
        assert response.status_code == 201
        created_note = response.json()
        note_id = created_note["id"]

        # Attempt to delete with an invalid token
        response = client.delete(
            f"/notes/{note_id}",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_note(self, client, login_user):
        token, user_id, email = login_user

        # Attempt to delete a note that does not exist
        response = client.delete(
            "/notes/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Note" in data["detail"]
