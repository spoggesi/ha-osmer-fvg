"""Sensor platform for OSMER FVG."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import DOMAIN, MONITORED_SENSORS, VERSION
from .coordinator import OsmerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OSMER sensors."""

    coordinator: OsmerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for sensor_code in coordinator.data.sensors:
        if sensor_code not in MONITORED_SENSORS:
            continue

        sensor_config = MONITORED_SENSORS[sensor_code]
        description = SensorEntityDescription(
            key=sensor_code,
            name=sensor_config["name"],
            native_unit_of_measurement=sensor_config["unit"],
            device_class=sensor_config["device_class"],
            state_class=sensor_config["state_class"],
            icon=sensor_config["icon"],
        )

        entities.append(
            OsmerSensor(
                coordinator,
                sensor_code,
                description,
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
        description: SensorEntityDescription,
    ) -> None:
        """Initialize sensor."""

        self.coordinator = coordinator
        self.sensor_code = sensor_code
        self.entity_description = description

        sensor = coordinator.data.sensors[sensor_code]
        station = coordinator.data.station

        self._attr_unique_id = f"osmer_{station.id}_{sensor.code}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""

        station = self.coordinator.data.station

        return DeviceInfo(
            identifiers={(DOMAIN, str(station.id))},
            name=f"OSMER {station.name}",
            manufacturer="OSMER FVG",
            model="Weather Station",
            configuration_url="https://monitor.protezionecivile.fvg.it",
            sw_version=VERSION,
        )

    @property
    def native_value(self) -> float | None:
        """Return sensor value."""

        measure = self.coordinator.data.measures.get(self.sensor_code)

        if measure is None:
            return None

        return measure.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

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
