"""Formatting helpers for OSMER config flow."""

from __future__ import annotations

from ..api.models import Sensor, Station
from ..helpers.distance import distance_km


def sensor_label(
    sensor: Sensor,
) -> str:
    """Return formatted sensor label."""

    icon = sensor_icon(
        sensor.code,
    )

    return f"{icon} {sensor.name}"


def station_label(
    station: Station,
    sensors: list[Sensor] | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> str:
    """Return formatted station label with unique sensor icons."""

    # Ensure sensors is always a list
    if sensors is None or not isinstance(sensors, list):
        sensors = []

    # Deduplica le icone per tipologia di sensore
    unique_icons: list[str] = []
    for sensor in sensors:
        icon = sensor_icon(sensor.code)
        if icon and icon not in unique_icons:
            unique_icons.append(icon)

    sensor_icons = "".join(unique_icons)

    if sensor_icons:
        sensor_text = f"{sensor_icons} "
    else:
        sensor_text = "📊 "  # Default icon if no sensors

    extra = []

    if latitude is not None and longitude is not None:
        distance = distance_km(
            latitude,
            longitude,
            station.latitude,
            station.longitude,
        )
        extra.append(f"📏 {distance:.1f} km")

    if station.altitude is not None:
        extra.append(f"⛰ {station.altitude} m")

    # Add station ID for clarity
    extra.append(f"ID: {station.id}")

    # Always show sensor count (0 or more)
    extra.append(f"{len(sensors)} sensori")

    if station.status:
        status_icon = "✅" if "attivo" in station.status.lower() else "❌"
        extra.append(f"{status_icon} {station.status}")

    if extra:
        return f"{sensor_text}{station.name} ({' | '.join(extra)})"

    return f"{sensor_text}{station.name}"


def sensor_icon(
    code: str,
) -> str:
    """Return icon associated with sensor."""

    code = code.lower()

    if "temp" in code:
        return "🌡"

    if "umid" in code or "hum" in code:
        return "💧"

    if "rain" in code or "piogg" in code or "prec" in code:
        return "🌧"

    if "vento" in code or "wind" in code:
        return "💨"

    if "press" in code or "baro" in code:
        return "🔵"

    return "📊"
