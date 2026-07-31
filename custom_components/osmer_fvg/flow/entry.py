"""Helpers for creating config entries."""

from __future__ import annotations

from typing import Any

from ..api.models import Station


def build_entry_data(
    station: Station,
    enabled_sensors: list[str],
) -> dict[str, Any]:
    """Build config entry data."""

    return {
        "station_id": station.id,
        "station_name": station.name,
        "enabled_sensors": enabled_sensors,
    }


def build_entry_title(
    station: Station,
) -> str:
    """Return config entry title."""

    return f"OSMER {station.name}"