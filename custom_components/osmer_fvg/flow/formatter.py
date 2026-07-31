"""Formatting helpers for the OSMER FVG config flow."""

from __future__ import annotations

from ..api.models import Sensor, Station

SENSOR_INFO: dict[str, dict[str, str]] = {
    "T": {
        "icon": "🌡",
        "label": "Temperatura",
    },
    "U": {
        "icon": "💧",
        "label": "Umidità",
    },
    "P": {
        "icon": "🌧",
        "label": "Pioggia",
    },
    "RR": {
        "icon": "🌦",
        "label": "Pioggia 24h",
    },
    "IDRO": {
        "icon": "🌊",
        "label": "Idrometro",
    },
}


def sensor_icon(code: str) -> str:
    """Return the icon associated with a sensor code."""

    return SENSOR_INFO.get(
        code,
        {},
    ).get(
        "icon",
        "📈",
    )


def sensor_display_name(code: str) -> str:
    """Return the human-readable name for a sensor code."""

    return SENSOR_INFO.get(
        code,
        {},
    ).get(
        "label",
        code,
    )


def sensor_icons(
    sensors: list[Sensor],
) -> str:
    """Return a compact string of sensor icons."""

    icons: list[str] = []

    for sensor in sensors:
        icon = sensor_icon(sensor.code)

        if icon not in icons:
            icons.append(icon)

    return "".join(icons)


def station_label(
    station: Station,
    sensors: list[Sensor],
) -> str:
    """Return the formatted label shown in the station selector."""

    return (
        f"{station.name}"
        f" • {int(station.altitude)} m"
        f" • {sensor_icons(sensors)}"
    )


def sensor_label(
    sensor: Sensor,
) -> str:
    """Return the formatted label shown in the sensor selector."""

    return (
        f"{sensor_icon(sensor.code)} "
        f"{sensor.name}"
    )


def confirmation_sensors(
    sensors: list[Sensor],
) -> str:
    """Return the sensor list shown in the confirmation page."""

    return "\n".join(
        f"✓ {sensor_label(sensor)}"
        for sensor in sensors
    )


def station_coordinates(
    station: Station,
) -> str:
    """Return formatted station coordinates."""

    return (
        f"{station.latitude:.5f}, "
        f"{station.longitude:.5f}"
    )