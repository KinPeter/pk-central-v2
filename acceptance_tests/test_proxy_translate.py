import pytest
import respx
from httpx import Response


class TestProxyTranslate:
    @respx.mock
    def test_success(self, client, login_user):
        token, user_id, email = login_user

        # Mock the DeepL API endpoint
        respx.post("https://api-free.deepl.com/v2/translate").mock(
            return_value=Response(
                200, json={"translations": [{"text": "Valid translation"}]}
            )
        )

        response = client.post(
            "/proxy/translate",
            json={"text": "hello", "source_lang": "en", "target_lang": "fr"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["translation"] == "Valid translation"
        assert data["original"] == "hello"
        assert data["sourceLang"] == "en"
        assert data["targetLang"] == "fr"

    @respx.mock
    def test_invalid_token(self, client):
        # Mock the DeepL API endpoint
        respx.post("https://api-free.deepl.com/v2/translate").mock(
            return_value=Response(
                200, json={"translations": [{"text": "Valid translation"}]}
            )
        )

        response = client.post(
            "/proxy/translate",
            json={"text": "hello", "source_lang": "en", "target_lang": "fr"},
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid token" in data["detail"]

    @pytest.mark.parametrize(
        "payload,expected_msg",
        [
            # Missing text
            ({"source_lang": "en", "target_lang": "fr"}, "Field required"),
            # Missing source_lang
            ({"text": "hello", "target_lang": "fr"}, "Field required"),
            # Missing target_lang
            ({"text": "hello", "source_lang": "en"}, "Field required"),
            # Empty text (min_length=1)
            (
                {"text": "", "source_lang": "en", "target_lang": "fr"},
                "at least 1 character",
            ),
            # Invalid source_lang
            (
                {"text": "hello", "source_lang": "xx", "target_lang": "fr"},
                "Input should be",
            ),
            # Invalid target_lang
            (
                {"text": "hello", "source_lang": "en", "target_lang": "yy"},
                "Input should be",
            ),
        ],
    )
    @respx.mock
    def test_invalid_request(self, client, login_user, payload, expected_msg):
        token, user_id, email = login_user
        # Mock the DeepL API endpoint (should not be called, but safe to mock)
        respx.post("https://api-free.deepl.com/v2/translate").mock(
            return_value=Response(
                200, json={"translations": [{"text": "Should not be called"}]}
            )
        )

        response = client.post(
            "/proxy/translate",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        assert expected_msg in data["detail"][0]["msg"]

    @respx.mock
    def test_deepl_api_error(self, client, login_user):
        token, user_id, email = login_user
        # Mock the DeepL API endpoint to return a 500 error
        respx.post("https://api-free.deepl.com/v2/translate").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        response = client.post(
            "/proxy/translate",
            json={"text": "hello", "source_lang": "en", "target_lang": "fr"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Internal Server Error" in data["detail"]
        assert "Translation failed" in data["detail"]
