"""Sensor platform for OSMER FVG."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

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


    entities = []


    for code in MONITORED_SENSORS:

        if code in coordinator.data.sensors:

            entities.append(
                OsmerSensor(
                    coordinator,
                    code,
                )
            )


    async_add_entities(
        entities
    )


class OsmerSensor(
    SensorEntity
):
    """Representation of an OSMER sensor."""


    _attr_has_entity_name = True


    def __init__(
        self,
        coordinator: OsmerDataUpdateCoordinator,
        sensor_code: str,
    ) -> None:
        """Initialize sensor."""

        self.coordinator = coordinator
        self.sensor_code = sensor_code


        sensor = coordinator.data.sensors[
            sensor_code
        ]


        self._sensor = sensor


        self._attr_unique_id = (
            f"osmer_{sensor.station_id}_{sensor.code}"
        )


        self._attr_name = (
            MONITORED_SENSORS[
                sensor_code
            ]["name"]
        )


        self._attr_native_unit_of_measurement = (
            sensor.unit
        )


        device_class = (
            MONITORED_SENSORS[
                sensor_code
            ].get(
                "device_class"
            )
        )


        if device_class:

            self._attr_device_class = (
                device_class
            )


    @property
    def native_value(
        self,
    ) -> float | None:
        """Return current value."""

        measure = (
            self.coordinator.data.measures.get(
                self.sensor_code
            )
        )


        if measure is None:
            return None


        return measure.value



    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return extra attributes."""

        station = (
            self.coordinator.data.station
        )


        return {
            "station": station.name,
            "station_id": station.id,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "altitude": station.altitude,
            "sensor_code": self.sensor_code,
            "sensor_name": self._sensor.name,
        }



    @property
    def device_info(self):
        """Return device information."""

        station = (
            self.coordinator.data.station
        )


        return {
            "identifiers": {
                (
                    "osmer_fvg",
                    str(station.id),
                )
            },
            "name": (
                f"OSMER {station.name}"
            ),
            "manufacturer": (
                "Protezione Civile FVG"
            ),
            "model": (
                "Weather Station"
            ),
            "sw_version": (
                station.status
            ),
        }