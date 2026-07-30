"""Parser for OSMER API responses."""

from .models import Station


def parse_station(data: dict) -> Station:
    """Convert station JSON into a Station object."""

    return Station(
        id=data["id"],
        name=data["name"],
        istat=data["istat"],
        latitude=data["lat"],
        longitude=data["lon"],
        elevation=data["alt"],
        status=data["status"],
    )