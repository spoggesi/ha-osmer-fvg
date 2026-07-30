"""Parser for OSMER API responses."""

from __future__ import annotations

from typing import Any

from .models import Station


def parse_station(data: dict[str, Any]) -> Station:
    """Parse a station response."""

    return Station(
        id=data["id"],
        name=data["name"],
        istat=data["istat"],
        latitude=data["lat"],
        longitude=data["lon"],
        altitude=data["alt"],
        status=data["status"],
    )