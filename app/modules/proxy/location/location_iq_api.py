import httpx


class LocationIqApi:
    """
    LocationIQ API client for geocoding and reverse geocoding.
    """

    def __init__(self, api_key: str, reverse_url: str):
        self.api_key = api_key
        self.reverse_url = reverse_url

    async def reverse_geocode(self, lat: float, lon: float) -> dict:
        """
        Reverse geocode latitude and longitude to get location details.
        """
        params = {
            "key": self.api_key,
            "lat": lat,
            "lon": lon,
            "format": "json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url=self.reverse_url, params=params)
            response.raise_for_status()
            return response.json()
