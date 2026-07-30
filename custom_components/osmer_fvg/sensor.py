"""Sensor platform for OSMER FVG."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import MONITORED_SENSORS
from .coordinator import (
    OsmerDataUpdateCoordinator,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OSMER sensors."""

    coordinator: OsmerDataUpdateCoordinator = hass.data["osmer_fvg"][entry.entry_id]

    entities: list[SensorEntity] = []

    for code in coordinator.data.sensors:
        if code not in MONITORED_SENSORS:
            continue

        entities.append(
            OsmerSensor(
                coordinator,
                code,
            )
        )

    async_add_entities(entities)


class OsmerSensor(
    SensorEntity,
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

        sensor = coordinator.data.sensors[sensor_code]

        station = coordinator.data.station

        self._attr_unique_id = f"osmer_{station.id}_{sensor.code}"

        self._attr_name = MONITORED_SENSORS[sensor.code]["name"]

        self._attr_native_unit_of_measurement = sensor.unit

        self._attr_device_class = self._get_device_class(sensor.code)

        self._attr_state_class = SensorStateClass.MEASUREMENT

        self._attr_icon = "mdi:weather-partly-cloudy"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""

        station = self.coordinator.data.station

        return DeviceInfo(
            identifiers={
                (
                    "osmer_fvg",
                    str(station.id),
                )
            },
            name=f"OSMER {station.name}",
            manufacturer="OSMER FVG",
            model="Weather Station",
            configuration_url=("https://monitor.protezionecivile.fvg.it"),
            sw_version="0.1.0",
        )

    @property
    def native_value(
        self,
    ) -> float | None:
        """Return current value."""

        measure = self.coordinator.data.measures.get(self.sensor_code)

        if measure is None:
            return None

        return measure.value

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return extra attributes."""

        station = self.coordinator.data.station

        sensor = self.coordinator.data.sensors[self.sensor_code]

        measure = self.coordinator.data.measures.get(self.sensor_code)

        return {
            "station": station.name,
            "station_id": station.id,
            "sensor_code": sensor.code,
            "sensor_name": sensor.name,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "altitude": station.altitude,
            "last_update": (measure.timestamp.isoformat() if measure else None),
        }

    @staticmethod
    def _get_device_class(
        code: str,
    ) -> SensorDeviceClass | None:
        """Return Home Assistant device class."""

        mapping = {
            "T": SensorDeviceClass.TEMPERATURE,
            "U": SensorDeviceClass.HUMIDITY,
            "RR": SensorDeviceClass.PRECIPITATION_INTENSITY,
            "P": SensorDeviceClass.PRECIPITATION,
        }

        return mapping.get(code)
