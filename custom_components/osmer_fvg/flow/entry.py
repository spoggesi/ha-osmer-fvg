"""Helpers for creating config entries."""

from __future__ import annotations

from typing import Any

from ..api.models import Station
from ..const import CONF_MULTI_STATION, CONF_STATION_IDS


def build_entry_data(
    station: Station | list[Station],
    enabled_sensors: list[str],
    multi_station: bool = False,
) -> dict[str, Any]:
    """Build config entry data."""

    if multi_station and isinstance(station, list):
        # Multi-station mode
        return {
            CONF_MULTI_STATION: True,
            CONF_STATION_IDS: [s.id for s in station],
            "station_names": [s.name for s in station],
            "enabled_sensors": enabled_sensors,
        }
    else:
        # Single station mode
        return {
            CONF_MULTI_STATION: False,
            "station_id": station.id,
            "station_name": station.name,
            "enabled_sensors": enabled_sensors,
        }


def build_entry_title(
    station: Station | list[Station],
    multi_station: bool = False,
) -> str:
    """Return config entry title."""

    if multi_station and isinstance(station, list):
        if len(station) == 1:
            return f"OSMER {station[0].name}"
        else:
            return f"OSMER Multi-Stazione ({len(station)} stazioni)"
    else:
        return f"OSMER {station.name}"
