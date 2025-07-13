import pytest
from unittest.mock import patch, MagicMock
import httpx
from app.modules.proxy.location.location_iq_api import LocationIqApi


@pytest.mark.asyncio
class TestLocationIqApi:
    def setup_method(self):
        self.api_key = "test-key"
        self.url = "https://locationiq.com/reverse"
        self.api = LocationIqApi(self.api_key, self.url)
        self.lat = 52.52
        self.lon = 13.405

    async def test_reverse_geocode_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"address": {"city": "Berlin"}}
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )
            result = await self.api.reverse_geocode(self.lat, self.lon)

            # Check request params
            called_args, called_kwargs = (
                mock_client.return_value.__aenter__.return_value.get.call_args
            )
            assert called_kwargs["url"] == self.url
            assert called_kwargs["params"]["key"] == self.api_key
            assert called_kwargs["params"]["lat"] == self.lat
            assert called_kwargs["params"]["lon"] == self.lon
            assert called_kwargs["params"]["format"] == "json"

            # Check result
            assert result == {"address": {"city": "Berlin"}}

    async def test_reverse_geocode_multiple_fields(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "address": {"city": "Paris", "country_code": "FR"}
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )
            result = await self.api.reverse_geocode(48.85, 2.35)
            assert result["address"]["city"] == "Paris"
            assert result["address"]["country_code"] == "FR"

    async def test_reverse_geocode_http_error(self):
        mock_response = MagicMock()
        request = httpx.Request("GET", self.url)
        response_obj = httpx.Response(400, request=request, text="API error")
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "API error", request=request, response=response_obj
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )
            with pytest.raises(httpx.HTTPStatusError) as exc:
                await self.api.reverse_geocode(self.lat, self.lon)
            assert "API error" in str(exc.value)
