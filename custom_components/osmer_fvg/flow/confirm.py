"""Confirmation helpers for the config flow."""

from __future__ import annotations

from typing import Any

from ..api.models import Sensor, Station


def build_description_placeholders(
    station: Station,
    sensors: list[Sensor],
) -> dict[str, Any]:
    """Return placeholders for the confirmation page."""

    enabled = "\n".join(
        f"✓ {sensor.name}"
        for sensor in sensors
    )

    return {
        "station": station.name,
        "latitude": str(
            station.latitude,
        ),
        "longitude": str(
            station.longitude,
        ),
        "altitude": f"{station.altitude} m",
        "sensor_count": str(
            len(sensors),
        ),
        "sensors": enabled,
    }