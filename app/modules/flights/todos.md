# Flights todos

## Aviation endpoints

- DB tables for aviation data from static files: aircrafts, airlines
- DB table for already visited airports, populate from migration
- search endpoints for aircrafts and airlines

## Flights endpoints

- Make most fields optional in the `Flight` model
- Airports, airlines and aircrafts should only expect iata/icao codes, get the full data from the DB
- For airports first check existing airports table, then use Gemini API to get the full airport data, fall back to Airlabs API + Location IQ if Gemini fails

## Gemini API

Example prompt for airport data:

```
Please look for information about the airport that has IATA code: CHQ.

The information I need:
- The ICAO code of the airport
- Coordinates as latitude and longitude of the airport in number format with decimals
- The official name of the airport in English if possible
- The city the airport is located at, using it's English name if possible. If there is no specific city then the nearest city or the region/state is also accepted.
- The 2 letter country code of the country the airport is located in.

Please respond in JSON format, for example:

{ "iata": "BUD", "icao": "LHBP", "name": "Liszt Ferenc International Airport", "city": "Budapest", "country": "HU", "lat": 19.223311, "lng": 41.1231123 }
```
