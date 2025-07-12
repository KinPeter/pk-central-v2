import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import Request
from app.modules.proxy.translate.translate import translate
from app.modules.proxy.translate.translate_types import (
    TranslationRequest,
    DeeplLanguage,
    Translation,
)


@pytest.mark.asyncio
async def test_translate_calls_deeplapi_with_correct_params():
    # Prepare mock env and logger
    env = MagicMock()
    env.DEEPL_API_KEY = "key"
    env.PROXY_DEEPL_TRANSLATE_URL = "url"
    logger = MagicMock()

    # Prepare request with app.state.env and app.state.logger
    request = MagicMock(spec=Request)
    request.app.state.env = env
    request.app.state.logger = logger

    # Prepare TranslationRequest
    body = TranslationRequest(
        text="hello",
        target_lang=DeeplLanguage.FR,
        source_lang=DeeplLanguage.EN,
    )

    # Prepare expected Translation
    expected_translation = Translation(
        original="hello",
        translation="bonjour",
        source_lang=DeeplLanguage.EN,
        target_lang=DeeplLanguage.FR,
    )

    with patch("app.modules.proxy.translate.translate.DeeplApi") as mock_deepl:
        mock_instance = mock_deepl.return_value
        mock_instance.translate_text = AsyncMock(return_value=expected_translation)

        result = await translate(request, body)

        # DeeplApi should be constructed with correct args
        mock_deepl.assert_called_once_with(
            api_key="key",
            translate_url="url",
            logger=logger,
        )
        # translate_text should be called with correct args
        mock_instance.translate_text.assert_called_once_with(
            text="hello",
            target_lang=DeeplLanguage.FR,
            source_lang=DeeplLanguage.EN,
        )
        # The result should be the expected Translation
        assert result == expected_translation


# Additional test for error case
import re
from app.common.responses import InternalServerErrorException


@pytest.mark.asyncio
async def test_translate_raises_internal_server_error_on_exception():
    env = MagicMock()
    env.DEEPL_API_KEY = "key"
    env.PROXY_DEEPL_TRANSLATE_URL = "url"
    logger = MagicMock()

    request = MagicMock(spec=Request)
    request.app.state.env = env
    request.app.state.logger = logger

    body = TranslationRequest(
        text="fail",
        target_lang=DeeplLanguage.FR,
        source_lang=DeeplLanguage.EN,
    )

    with patch("app.modules.proxy.translate.translate.DeeplApi") as mock_deepl:
        mock_instance = mock_deepl.return_value
        mock_instance.translate_text = AsyncMock(side_effect=Exception("deepl error"))

        with pytest.raises(InternalServerErrorException) as exc_info:
            await translate(request, body)
        # Check that the error message contains the expected text
        assert re.search(
            r"Translation failed due to error:.*deepl error", str(exc_info.value)
        )
        logger.error.assert_called()
