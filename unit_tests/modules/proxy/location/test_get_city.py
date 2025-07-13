import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import Request
from app.modules.proxy.location.get_city import get_city
from app.modules.proxy.location.location_types import CityLocation
from app.common.responses import NotFoundException, InternalServerErrorException


@pytest.mark.asyncio
@patch("app.modules.proxy.location.get_city.LocationIqApi")
@patch("app.modules.proxy.location.get_city.CountryData")
async def test_get_city_success(mock_country_data, mock_location_api):
    env = MagicMock()
    env.PROXY_LOCATION_REVERSE_URL = "dummy_url"
    env.LOCATION_IQ_API_KEY = "dummy_key"
    logger = MagicMock()

    request = MagicMock(spec=Request)
    request.app.state.env = env
    request.app.state.logger = logger

    mock_api_instance = mock_location_api.return_value
    mock_api_instance.reverse_geocode = AsyncMock(
        return_value={"address": {"city": "Berlin", "country_code": "DE"}}
    )
    mock_country_data.return_value.get_name.return_value = "Germany"

    result = await get_city(request, 52.52, 13.405)
    assert isinstance(result, CityLocation)
    assert result.city == "Berlin"
    assert result.country == "Germany"
    assert result.lat == 52.52
    assert result.lng == 13.405
    logger.error.assert_not_called()


@pytest.mark.asyncio
@patch("app.modules.proxy.location.get_city.LocationIqApi")
async def test_get_city_address_not_found(mock_location_api):
    env = MagicMock()
    env.PROXY_LOCATION_REVERSE_URL = "dummy_url"
    env.LOCATION_IQ_API_KEY = "dummy_key"
    logger = MagicMock()
    request = MagicMock(spec=Request)
    request.app.state.env = env
    request.app.state.logger = logger

    mock_api_instance = mock_location_api.return_value
    mock_api_instance.reverse_geocode = AsyncMock(return_value={})

    with pytest.raises(NotFoundException):
        await get_city(request, 0, 0)
    logger.error.assert_called_with("Address not found for coordinates: 0, 0")


@pytest.mark.asyncio
@patch("app.modules.proxy.location.get_city.LocationIqApi")
@patch("app.modules.proxy.location.get_city.CountryData")
async def test_get_city_countrydata_raises(mock_country_data, mock_location_api):
    env = MagicMock()
    env.PROXY_LOCATION_REVERSE_URL = "dummy_url"
    env.LOCATION_IQ_API_KEY = "dummy_key"
    logger = MagicMock()
    request = MagicMock(spec=Request)
    request.app.state.env = env
    request.app.state.logger = logger

    mock_api_instance = mock_location_api.return_value
    mock_api_instance.reverse_geocode = AsyncMock(
        return_value={"address": {"city": "Paris", "country_code": "FR"}}
    )
    mock_country_data.return_value.get_name.side_effect = Exception("fail")

    with pytest.raises(InternalServerErrorException):
        await get_city(request, 48.85, 2.35)
    logger.error.assert_called()


# Additional test: LocationIqApi raises an error
@pytest.mark.asyncio
@patch("app.modules.proxy.location.get_city.LocationIqApi")
@patch("app.modules.proxy.location.get_city.CountryData")
async def test_get_city_locationiqapi_raises(mock_country_data, mock_location_api):
    env = MagicMock()
    env.PROXY_LOCATION_REVERSE_URL = "dummy_url"
    env.LOCATION_IQ_API_KEY = "dummy_key"
    logger = MagicMock()
    request = MagicMock(spec=Request)
    request.app.state.env = env
    request.app.state.logger = logger

    mock_api_instance = mock_location_api.return_value
    mock_api_instance.reverse_geocode = AsyncMock(side_effect=Exception("api fail"))
    mock_country_data.return_value.get_name.return_value = "Germany"

    with pytest.raises(InternalServerErrorException) as exc_info:
        await get_city(request, 1.0, 2.0)
    logger.error.assert_called()
    assert "api fail" in str(exc_info.value)
