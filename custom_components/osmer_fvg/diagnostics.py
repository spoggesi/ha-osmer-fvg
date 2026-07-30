"""Diagnostics support for OSMER FVG."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import (
    OsmerDataUpdateCoordinator,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for an OSMER config entry."""

    coordinator: OsmerDataUpdateCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )


    station = coordinator.data.station


    sensors = {}

    for code, sensor in coordinator.data.sensors.items():

        measure = (
            coordinator.data.measures.get(code)
        )

        sensors[code] = {
            "name": sensor.name,
            "unit": sensor.unit,
            "value": (
                measure.value
                if measure
                else None
            ),
            "timestamp": (
                measure.timestamp.isoformat()
                if measure
                else None
            ),
        }


    return {
        "station": {
            "id": station.id,
            "name": station.name,
            "istat": station.istat,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "altitude": station.altitude,
            "status": station.status,
        },
        "sensors": sensors,
        "last_update": (
            coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time
            else None
        ),
    }