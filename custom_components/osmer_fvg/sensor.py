"""Sensor platform for OSMER FVG."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import OsmerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OSMER sensors from config entry."""

    coordinator: OsmerDataUpdateCoordinator = (
        hass.data["osmer_fvg"][entry.entry_id]
    )

    entities = [
        OsmerStationSensor(
            coordinator,
            station.id,
        )
        for station in coordinator.data
    ]

    async_add_entities(entities)


class OsmerStationSensor(SensorEntity):
    """Representation of an OSMER station."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(
        self,
        coordinator: OsmerDataUpdateCoordinator,
        station_id: int,
    ) -> None:
        """Initialize sensor."""

        self.coordinator = coordinator
        self.station_id = station_id

        self._attr_unique_id = (
            f"osmer_fvg_station_{station_id}"
        )

    @property
    def native_value(self) -> str | None:
        """Return sensor value."""

        station = self._get_station()

        if station is None:
            return None

        return station.name

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return station attributes."""

        station = self._get_station()

        if station is None:
            return {}

        return {
            "latitude": station.latitude,
            "longitude": station.longitude,
            "altitude": station.altitude,
            "status": station.status,
        }

    def _get_station(self):
        """Return current station."""

        return next(
            (
                station
                for station in self.coordinator.data
                if station.id == self.station_id
            ),
            None,
        )