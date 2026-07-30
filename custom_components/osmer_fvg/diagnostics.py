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

    coordinator: OsmerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    data = coordinator.data

    if data is None:
        return {
            "error": "No coordinator data available",
        }

    station = data.station

    sensors: dict[str, Any] = {}

    for code, sensor in data.sensors.items():
        measure = data.measures.get(code)

        sensors[code] = {
            "id": sensor.id,
            "name": sensor.name,
            "unit": sensor.unit,
            "status": sensor.status,
            "value": (measure.value if measure else None),
            "timestamp": (measure.timestamp.isoformat() if measure else None),
        }

    device_info = {
        "manufacturer": "OSMER FVG",
        "model": "Weather Station",
        "station_id": station.id,
    }

    return {
        "integration": {
            "domain": DOMAIN,
            "version": "0.1.0",
        },
        "config_entry": {
            "title": entry.title,
            "entry_id": entry.entry_id,
            "created_at": (entry.created_at.isoformat() if entry.created_at else None),
        },
        "device": device_info,
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
        "coordinator": {
            "last_update": (
                coordinator.last_update_success_time.isoformat()
                if coordinator.last_update_success_time
                else None
            ),
            "update_interval": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "last_exception": (
                str(coordinator.last_exception) if coordinator.last_exception else None
            ),
        },
    }
