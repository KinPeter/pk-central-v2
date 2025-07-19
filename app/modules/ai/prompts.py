def airport_data_prompt(iata_code: str):
    return f"""
Please act as a travel professional and look for information about the airport that has IATA code: {iata_code}.
Make sure the IATA code exactly matches the airport you are looking for. Only return the information if the airports IATA code is exactly {iata_code}.

You should find the following information about the airport:
- The ICAO code of the airport
- Coordinates as latitude and longitude of the airport in number format with decimals
- The official name of the airport in English if possible
- The city the airport is located at, using its English name if possible. If there is no specific city then the nearest city or the region/state is also accepted.
- The English name of the country the airport is located in.

Make sure to respond in JSON format, for example:
{{ "iata": "BUD", "icao": "LHBP", "name": "Liszt Ferenc International Airport", "city": "Budapest", "country": "Hungary", "lat": 19.223311, "lng": 41.1231123 }}
"""
