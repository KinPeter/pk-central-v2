import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from logging import Logger
from app.modules.ai.gemini_api import GeminiApi


@pytest.fixture
def mock_logger():
    return MagicMock(spec=Logger)


@pytest.mark.asyncio
@patch("app.modules.ai.gemini_api.genai.Client")
async def test_generate_json_success(mock_client_class, mock_logger):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_aio = MagicMock()
    mock_models = MagicMock()
    mock_generate_content = AsyncMock(
        return_value=MagicMock(text='```json\n{"iata": "BUD"}\n```')
    )
    mock_models.generate_content = mock_generate_content
    mock_aio.models = mock_models
    mock_client.aio = mock_aio

    api = GeminiApi(api_key="test-key", logger=mock_logger)
    result = await api.generate_json(prompt="prompt", model="model")
    assert result == {"iata": "BUD"}
    mock_generate_content.assert_awaited_once()
    mock_logger.error.assert_not_called()


@pytest.mark.asyncio
@patch("app.modules.ai.gemini_api.genai.Client")
async def test_generate_json_no_text(mock_client_class, mock_logger):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_aio = MagicMock()
    mock_models = MagicMock()
    mock_generate_content = AsyncMock(return_value=MagicMock(text=None))
    mock_models.generate_content = mock_generate_content
    mock_aio.models = mock_models
    mock_client.aio = mock_aio

    api = GeminiApi(api_key="test-key", logger=mock_logger)
    with pytest.raises(
        ValueError, match="No response text received from the Gemini API."
    ):
        await api.generate_json(prompt="prompt", model="model")
    mock_logger.error.assert_called()


@patch("app.modules.ai.gemini_api.genai.Client")
def test_extract_json_success(mock_client_class, mock_logger):
    api = GeminiApi(api_key="test-key", logger=mock_logger)
    text = 'some text before {"iata": "BUD"} some text after'
    result = api.extract_json(text)
    assert result == {"iata": "BUD"}
    mock_logger.error.assert_not_called()


@patch("app.modules.ai.gemini_api.genai.Client")
def test_extract_json_no_json(mock_client_class, mock_logger):
    api = GeminiApi(api_key="test-key", logger=mock_logger)
    text = "no json here"
    with pytest.raises(ValueError, match="No valid JSON found in the response."):
        api.extract_json(text)
    mock_logger.error.assert_called()


@patch("app.modules.ai.gemini_api.genai.Client")
def test_extract_json_invalid_json(mock_client_class, mock_logger):
    api = GeminiApi(api_key="test-key", logger=mock_logger)
    text = "{invalid json}"
    with pytest.raises(ValueError, match="Invalid JSON format"):
        api.extract_json(text)
    mock_logger.error.assert_called()
