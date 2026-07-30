"""Sensor icon helper."""

from __future__ import annotations

from custom_components.osmer_fvg.api.models import Sensor

ICON_MAP: dict[str, str] = {
    "T": "🌡",
    "U": "💧",
    "RR": "🌧",
    "P": "🌧",
    "Prec_24_ore": "☔",
    "IDRO": "🌊",
    "VV": "🌬",
    "RAD": "☀",
}


def get_sensor_icons(
    sensors: list[Sensor],
) -> str:
    """Return emoji string describing available sensors."""

    icons: list[str] = []

    for sensor in sensors:
        icon = ICON_MAP.get(sensor.code)

        if icon and icon not in icons:
            icons.append(icon)

    return "".join(icons)