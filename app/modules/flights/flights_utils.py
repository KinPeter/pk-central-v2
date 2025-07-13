from app.modules.flights.flights_types import Flight


def to_flight(item: dict) -> Flight:
    return Flight(
        id=item["id"],
        created_at=item["created_at"],
        flight_number=item["flight_number"],
        date=item["date"],
        departure_airport=item["departure_airport"],
        arrival_airport=item["arrival_airport"],
        departure_time=item["departure_time"],
        arrival_time=item["arrival_time"],
        duration=item["duration"],
        distance=item["distance"],
        airline=item["airline"],
        aircraft=item["aircraft"],
        registration=item.get("registration"),
        seat_number=item.get("seat_number"),
        seat_type=item.get("seat_type"),
        flight_class=item.get("flight_class"),
        flight_reason=item.get("flight_reason"),
        note=item.get("note"),
        is_planned=item.get("is_planned", False),
    )
