"""Forecast zone resolver for OSMER FVG."""

from __future__ import annotations

from .helpers.distance import distance_km

ZONE_CENTROIDS = {
    "Z1": {"name": "Monti", "lat": 46.40, "lon": 12.90},
    "Z2": {"name": "Alta Pianura", "lat": 46.10, "lon": 13.10},
    "Z3": {"name": "Bassa Pianura", "lat": 45.85, "lon": 13.15},
    "Z4": {"name": "Costa e Carso", "lat": 45.70, "lon": 13.60},
}


def get_osmer_zone(
    latitude: float,
    longitude: float,
    altitude: float,
) -> str:
    """Return the OSMER forecast zone code for given station coordinates."""

    if altitude >= 500.0:
        return "Z1"

    closest_zone = "Z2"
    min_dist = float("inf")

    for zone_code, data in ZONE_CENTROIDS.items():
        dist = distance_km(latitude, longitude, data["lat"], data["lon"])
        if dist < min_dist:
            min_dist = dist
            closest_zone = zone_code

    return closest_zone
