# Flights todos

## Aviation endpoints

- DB table for already visited airports, populate from migration

## Flights endpoints

- Make most fields optional in the `Flight` model
- Airports, airlines and aircrafts should only expect iata/icao codes, get the full data from the DB
- For airports first check existing airports table, then use Gemini API to get the full airport data, fall back to Airlabs API + Location IQ if Gemini fails
