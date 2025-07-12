import pytest
from unittest.mock import patch, MagicMock
import httpx
from app.modules.proxy.translate.deepl_api import DeeplApi
from app.modules.proxy.translate.translate_types import DeeplLanguage, Translation


@pytest.mark.asyncio
class TestDeeplApi:
    def setup_method(self):
        self.api_key = "test-key"
        self.url = "https://api.deepl.com/v2/translate"
        self.logger = MagicMock()
        self.deepl = DeeplApi(self.api_key, self.url, self.logger)
        self.text = "Hello"
        self.target_lang = DeeplLanguage.FR
        self.source_lang = DeeplLanguage.EN

    async def test_translate_text_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"translations": [{"text": "Bonjour"}]}
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )
            result = await self.deepl.translate_text(
                self.text, self.target_lang, self.source_lang
            )

            # Check request body
            called_args, called_kwargs = (
                mock_client.return_value.__aenter__.return_value.post.call_args
            )
            assert called_kwargs["url"] == self.url
            assert (
                called_kwargs["headers"]["Authorization"]
                == f"DeepL-Auth-Key {self.api_key}"
            )
            assert called_kwargs["json"]["text"] == [self.text]
            assert called_kwargs["json"]["target_lang"] == "FR"
            assert called_kwargs["json"]["source_lang"] == "EN"

            # Check result
            assert isinstance(result, Translation)
            assert result.original == self.text
            assert result.translation == "Bonjour"
            assert result.source_lang == self.source_lang
            assert result.target_lang == self.target_lang

    async def test_translate_text_multiple_translations(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "translations": [{"text": "Bonjour"}, {"text": "Salut"}]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )
            result = await self.deepl.translate_text(
                self.text, self.target_lang, self.source_lang
            )
            assert result.translation == "Bonjour Salut"

    async def test_translate_text_api_error(self):
        mock_response = MagicMock()
        # Simulate httpx.HTTPStatusError
        request = httpx.Request("POST", self.url)
        response_obj = httpx.Response(400, request=request, text="API error")
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "API error", request=request, response=response_obj
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )
            with pytest.raises(httpx.HTTPStatusError) as exc:
                await self.deepl.translate_text(
                    self.text, self.target_lang, self.source_lang
                )
            assert "API error" in str(exc.value)
            self.logger.error.assert_called()
