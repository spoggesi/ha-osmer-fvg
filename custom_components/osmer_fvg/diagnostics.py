"""Diagnostics for OSMER FVG integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics data for a config entry.
    
    This data will be available in:
    Settings -> Devices & Services -> OSMER FVG -> Diagnostics
    """
    from .coordinator import OsmerDataUpdateCoordinator
    
    # Get coordinator from entry
    coordinator: OsmerDataUpdateCoordinator | None = hass.data[DOMAIN].get(
        entry.entry_id
    )
    
    if coordinator is None:
        return {
            "error": "Coordinator not initialized",
            "entry_id": entry.entry_id,
            "data": entry.data,
            "options": entry.options,
        }
    
    # Collect diagnostics data
    diagnostics_data = {
        "entry_id": entry.entry_id,
        "station_id": entry.data.get("station_id"),
        "station_name": entry.data.get("station_name"),
        "enabled_sensors": entry.options.get(
            "enabled_sensors", entry.data.get("enabled_sensors", [])
        ),
        "options": {
            "scan_interval": entry.options.get("scan_interval", 15),
            "retry_count": entry.options.get("retry_count", 3),
            "retry_delay": entry.options.get("retry_delay", 5),
            "timeout": entry.options.get("timeout", 30),
            "offline_threshold": entry.options.get("offline_threshold", 30),
        },
        "coordinator": {
            "is_offline": coordinator.is_offline,
            "last_update_success": (
                coordinator.osmer_last_update_success.isoformat()
                if coordinator.osmer_last_update_success
                else None
            ),
            "update_interval": str(coordinator.update_interval),
        },
    }
    
    # Add station data if available
    if coordinator.data and coordinator.data.station:
        station = coordinator.data.station
        diagnostics_data["station"] = {
            "id": station.id,
            "name": station.name,
            "istat": station.istat,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "altitude": station.altitude,
            "status": station.status,
        }
    
    # Add sensor data if available
    if coordinator.data and coordinator.data.sensors:
        diagnostics_data["sensors"] = {
            "total": len(coordinator.data.sensors),
            "active": list(coordinator.data.sensors.keys()),
        }
    
    # Add measures data if available
    if coordinator.data and coordinator.data.measures:
        diagnostics_data["measures"] = {
            "total": len(coordinator.data.measures),
            "sensors_with_data": list(coordinator.data.measures.keys()),
        }
    
    # Add forecasts data if available
    if coordinator.data and coordinator.data.forecasts:
        diagnostics_data["forecasts"] = {
            "count": len(coordinator.data.forecasts),
        }
    
    # Add alerts data if available
    if coordinator.data and coordinator.data.alerts:
        diagnostics_data["alerts"] = {
            "count": len(coordinator.data.alerts),
            "active": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "level": alert.level,
                    "type": alert.type,
                }
                for alert in coordinator.data.alerts
            ],
        }
    
    # Add version info
    from .const import VERSION
    diagnostics_data["version"] = {
        "integration": VERSION,
        "home_assistant": hass.version,
    }
    
    # Add cache info
    diagnostics_data["cache"] = {
        "loaded": coordinator._cache_loaded,
        "data_present": bool(coordinator._cache_data),
        "version": coordinator._cache_data.get("version") if coordinator._cache_data else None,
    }
    
    return diagnostics_data
