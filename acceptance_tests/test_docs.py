import pytest


class TestCreateAndGetDocuments:
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Create a document
        doc_data = {
            "title": "My First Document",
            "content": "This is the content of my first document.",
            "tags": ["important", "work"],
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 201
        created_doc = response.json()
        assert created_doc["title"] == doc_data["title"]
        assert created_doc["content"] == doc_data["content"]
        assert created_doc["tags"] == doc_data["tags"]
        assert "id" in created_doc

        # Create another document (no tags)
        doc_data2 = {
            "title": "Second Document",
            "content": "Content for the second document.",
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data2,
        )
        assert response.status_code == 201
        created_doc2 = response.json()
        assert created_doc2["title"] == doc_data2["title"]
        assert created_doc2["content"] == doc_data2["content"]
        assert created_doc2["tags"] == []

        # Get all documents (list endpoint - content not included)
        response = client.get(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        entities = data["entities"]
        assert len(entities) == 2
        assert entities[0]["title"] == doc_data["title"]
        assert entities[0]["tags"] == doc_data["tags"]
        assert "content" not in entities[0]  # Content should not be in list
        assert entities[1]["title"] == doc_data2["title"]
        assert entities[1]["tags"] == []
        assert "content" not in entities[1]

    def test_create_invalid_token(self, client, login_user):
        # Create with invalid token
        response = client.post(
            "/docs/",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "title": "Test Document",
                "content": "Test content",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_get_documents_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        doc_data = {
            "title": "Test Document",
            "content": "Test content",
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 201
        # Get with invalid token
        response = client.get(
            "/docs/",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "doc_data,expected_msg",
        [
            # Title too short
            (
                {"title": "", "content": "Some content"},
                "at least 1 character",
            ),
            # Title too long
            (
                {"title": "a" * 257, "content": "Some content"},
                "at most 256 characters",
            ),
            # Content too short
            (
                {"title": "Valid Title", "content": ""},
                "at least 1 character",
            ),
            # Tag too short
            (
                {"title": "Valid Title", "content": "Valid content", "tags": [""]},
                "at least 1 character",
            ),
            # Tag too long
            (
                {
                    "title": "Valid Title",
                    "content": "Valid content",
                    "tags": ["a" * 17],
                },
                "at most 16 characters",
            ),
            # Missing required fields
            (
                {"content": "Some content"},
                "Field required",
            ),
            (
                {"title": "Valid Title"},
                "Field required",
            ),
        ],
    )
    def test_create_invalid_data(self, client, login_user, doc_data, expected_msg):
        token, user_id, email = login_user
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestGetDocumentById:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        # Create a document first
        doc_data = {
            "title": "Test Document",
            "content": "This is the full content of the document.",
            "tags": ["test", "sample"],
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 201
        doc_id = response.json()["id"]

        # Get the document by ID (content should be included)
        response = client.get(
            f"/docs/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        doc = response.json()
        assert doc["id"] == doc_id
        assert doc["title"] == doc_data["title"]
        assert doc["content"] == doc_data["content"]
        assert doc["tags"] == doc_data["tags"]

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        doc_data = {
            "title": "Test Document",
            "content": "Test content",
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 201
        doc_id = response.json()["id"]

        # Get with invalid token
        response = client.get(
            f"/docs/{doc_id}",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_document(self, client, login_user):
        token, user_id, email = login_user
        response = client.get(
            "/docs/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Document" in data["detail"]


class TestUpdateDocument:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        # Create first
        doc_data = {
            "title": "Original Title",
            "content": "Original content",
            "tags": ["original"],
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 201
        created_doc = response.json()
        doc_id = created_doc["id"]

        # Update
        update_data = {
            "title": "Updated Title",
            "content": "Updated content with more information.",
            "tags": ["updated", "modified", "v2"],
        }
        response = client.put(
            f"/docs/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 200
        updated_doc = response.json()
        assert updated_doc["id"] == doc_id
        assert updated_doc["title"] == update_data["title"]
        assert updated_doc["content"] == update_data["content"]
        assert updated_doc["tags"] == update_data["tags"]

        # Get all to verify
        response = client.get(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert len(entities) == 1
        assert any(
            e["id"] == doc_id and e["title"] == update_data["title"] for e in entities
        )

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        doc_data = {
            "title": "Test Document",
            "content": "Test content",
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 201
        doc_id = response.json()["id"]

        update_data = {
            "title": "Updated Title",
            "content": "Updated content",
        }
        response = client.put(
            f"/docs/{doc_id}",
            headers={"Authorization": "Bearer invalid_token"},
            json=update_data,
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_document(self, client, login_user):
        token, user_id, email = login_user
        update_data = {
            "title": "Updated Title",
            "content": "Updated content",
        }
        response = client.put(
            "/docs/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Document" in data["detail"]

    @pytest.mark.parametrize(
        "update_data,expected_msg",
        [
            # Title too short
            (
                {"title": "", "content": "Some content"},
                "at least 1 character",
            ),
            # Title too long
            (
                {"title": "a" * 257, "content": "Some content"},
                "at most 256 characters",
            ),
            # Content too short
            (
                {"title": "Valid Title", "content": ""},
                "at least 1 character",
            ),
            # Tag too short
            (
                {"title": "Valid Title", "content": "Valid content", "tags": [""]},
                "at least 1 character",
            ),
            # Tag too long
            (
                {
                    "title": "Valid Title",
                    "content": "Valid content",
                    "tags": ["a" * 17],
                },
                "at most 16 characters",
            ),
            # Missing required fields
            (
                {"content": "Some content"},
                "Field required",
            ),
            (
                {"title": "Valid Title"},
                "Field required",
            ),
        ],
    )
    def test_invalid_data(self, client, login_user, update_data, expected_msg):
        token, user_id, email = login_user
        doc_data = {
            "title": "Original Title",
            "content": "Original content",
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 201
        doc_id = response.json()["id"]

        response = client.put(
            f"/docs/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert response.status_code == 422
        data = response.json()
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]


class TestDeleteDocument:
    def test_success(self, client, login_user):
        token, user_id, email = login_user
        doc_data = {
            "title": "Document To Delete",
            "content": "This document will be deleted.",
            "tags": ["temporary"],
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 201
        doc_id = response.json()["id"]

        response = client.delete(
            f"/docs/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id

        # Verify deletion
        response = client.get(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        entities = response.json()["entities"]
        assert len(entities) == 0

    def test_invalid_token(self, client, login_user):
        token, user_id, email = login_user
        doc_data = {
            "title": "Document To Delete",
            "content": "Test content",
        }
        response = client.post(
            "/docs/",
            headers={"Authorization": f"Bearer {token}"},
            json=doc_data,
        )
        assert response.status_code == 201
        doc_id = response.json()["id"]

        response = client.delete(
            f"/docs/{doc_id}",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    def test_nonexistent_document(self, client, login_user):
        token, user_id, email = login_user
        response = client.delete(
            "/docs/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found: Document" in data["detail"]
