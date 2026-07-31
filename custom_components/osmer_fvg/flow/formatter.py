"""Formatting helpers for the OSMER FVG config flow."""

from __future__ import annotations

from ..api.models import Sensor, Station

SENSOR_INFO = {

    "T": "🌡️",
    "U": "💧",

    "RR": "🌧️",
    "P": "🌧️",
    "P_1h": "🌧️",

    "Prec_5_min": "🌧️",
    "Prec_60_min": "🌧️",
    "Prec_3_ore": "🌧️",
    "Prec_6_ore": "🌧️",
    "Prec_12_ore": "🌧️",
    "Prec_24_ore": "🌧️",
    "Prec_48_ore": "🌧️",

    "IDRO": "🌊",

    "CAR": "🔋",
    "SCAR": "🔋",

    "STSpluv (RAW)": "⚙️",
}


def sensor_icon(
    code: str,
) -> str:
    """Return icon."""

    return SENSOR_INFO.get(
        code,
        "📈",
    )


def sensor_icons(
    sensors: list[Sensor],
) -> str:
    """Return sensor icons."""

    icons = []

    for sensor in sensors:

        icon = sensor_icon(
            sensor.code,
        )

        if icon not in icons:
            icons.append(icon)

    return "".join(icons)



def station_label(
    station: Station,
    sensors: list[Sensor],
) -> str:
    """Station selector label."""

    return (
        f"{station.name}"
        f" • {int(station.altitude)} m"
        f" • {sensor_icons(sensors)}"
    )



def sensor_label(
    sensor: Sensor,
) -> str:
    """Sensor selector label."""

    return (
        f"{sensor_icon(sensor.code)} "
        f"{sensor.name}"
    )



def confirmation_sensors(
    sensors: list[Sensor],
) -> str:
    """Confirmation list."""

    return "\n".join(
        f"✓ {sensor_label(sensor)}"
        for sensor in sensors
    )



def station_coordinates(
    station: Station,
) -> str:
    """Coordinates."""

    return (
        f"{station.latitude:.5f}, "
        f"{station.longitude:.5f}"
    )