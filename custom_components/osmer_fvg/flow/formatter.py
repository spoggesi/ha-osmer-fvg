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
    """Return formatted station label."""

    sensors = sensors or []

    sensor_icons = "".join(
        sensor_icon(
            sensor.code,
        )
        for sensor in sensors
    )

    if sensor_icons:
        sensor_text = f"{sensor_icons} "
    else:
        sensor_text = ""


    extra = []


    if latitude is not None and longitude is not None:

        distance = distance_km(
            latitude,
            longitude,
            station.latitude,
            station.longitude,
        )

        extra.append(
            f"📏 {distance:.1f} km"
        )


    if getattr(
        station,
        "altitude",
        None,
    ) is not None:

        extra.append(
            f"⛰ {station.altitude} m"
        )


    if sensors:

        extra.append(
            f"{len(sensors)} sensori"
        )


    if extra:

        return (
            f"{sensor_text}"
            f"{station.name} "
            f"({' | '.join(extra)})"
        )


    return (
        f"{sensor_text}"
        f"{station.name}"
    )


def sensor_icon(
    code: str,
) -> str:
    """Return icon associated with sensor."""

    code = code.lower()


    if "temp" in code:

        return "🌡"


    if (
        "umid" in code
        or "hum" in code
    ):

        return "💧"


    if (
        "rain" in code
        or "piogg" in code
        or "prec" in code
    ):

        return "🌧"


    if (
        "vento" in code
        or "wind" in code
    ):

        return "💨"


    if (
        "press" in code
        or "baro" in code
    ):

        return "🔵"


    return "📊"