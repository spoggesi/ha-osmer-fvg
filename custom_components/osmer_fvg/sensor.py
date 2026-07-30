"""Sensor platform for OSMER FVG."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MONITORED_SENSORS
from .coordinator import OsmerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OSMER sensors."""

    coordinator: OsmerDataUpdateCoordinator = (
        hass.data["osmer_fvg"][entry.entry_id]
    )

    entities = [
        OsmerSensor(
            coordinator,
            code,
        )
        for code in coordinator.data.sensors
    ]

    async_add_entities(entities)


class OsmerSensor(SensorEntity):
    """Representation of an OSMER measurement."""

    _attr_has_entity_name = True


    def __init__(
        self,
        coordinator: OsmerDataUpdateCoordinator,
        sensor_code: str,
    ) -> None:
        """Initialize sensor."""

        self.coordinator = coordinator
        self.sensor_code = sensor_code

        config = MONITORED_SENSORS[sensor_code]

        self._attr_name = config["name"]

        self._attr_unique_id = (
            f"osmer_fvg_"
            f"{coordinator.station_id}_"
            f"{sensor_code}"
        )


        self._attr_icon = (
            "mdi:weather-partly-cloudy"
        )


    @property
    def native_value(
        self,
    ) -> float | None:
        """Return latest value."""

        measure = (
            self.coordinator.data.measures
            .get(self.sensor_code)
        )


        if measure is None:
            return None


        return measure.value


    @property
    def native_unit_of_measurement(
        self,
    ) -> str | None:
        """Return unit."""

        sensor = (
            self.coordinator.data.sensors
            .get(self.sensor_code)
        )


        if sensor is None:
            return None


        return sensor.unit


    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return extra attributes."""

        station = (
            self.coordinator.data.station
        )


        measure = (
            self.coordinator.data.measures
            .get(self.sensor_code)
        )


        return {
            "station": station.name,
            "station_id": station.id,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "altitude": station.altitude,
            "last_update": (
                measure.timestamp.isoformat()
                if measure
                else None
            ),
        }