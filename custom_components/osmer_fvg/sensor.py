"""Sensor platform for OSMER FVG."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    EntityCategory,
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

_LOGGER = logging.getLogger(__name__)


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

    # Add last update timestamp sensor
    timestamp_description = SensorEntityDescription(
        key="last_update",
        name="Ultimo aggiornamento",
        device_class=None,
        state_class=None,
        icon="mdi:clock-outline",
    )
    entities.append(
        OsmerLastUpdateSensor(
            coordinator,
            timestamp_description,
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
        self._last_known_value: float | None = None
        self._last_known_timestamp: str | None = None

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
        """Return sensor value (with offline support)."""

        measure = self.coordinator.data.measures.get(self.sensor_code)

        if measure is not None:
            # Update last known value
            self._last_known_value = measure.value
            self._last_known_timestamp = measure.timestamp.isoformat()
            return measure.value

        # If no measure, return last known value if available (offline mode)
        if self._last_known_value is not None and self.coordinator.is_offline:
            _LOGGER.debug(
                "Sensor %s returning last known value (offline mode): %s",
                self._attr_unique_id,
                self._last_known_value,
            )
            return self._last_known_value

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        station = self.coordinator.data.station
        sensor = self.coordinator.data.sensors[self.sensor_code]
        measure = self.coordinator.data.measures.get(self.sensor_code)

        attrs = {
            "station": station.name,
            "station_id": station.id,
            "sensor_code": sensor.code,
            "sensor_name": sensor.name,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "altitude": station.altitude,
            "last_update": (measure.timestamp.isoformat() if measure else None),
            "last_known_value": self._last_known_value,
            "last_known_timestamp": self._last_known_timestamp,
            "is_offline": self.coordinator.is_offline,
            "offline_since": (
                self.coordinator.osmer_last_update_success.isoformat()
                if self.coordinator.is_offline and self.coordinator.osmer_last_update_success
                else None
            ),
        }
        
        return attrs

    async def async_added_to_hass(self) -> None:
        """Initialize last known value when entity is added."""
        await super().async_added_to_hass()
        
        # Initialize last known value from current data
        measure = self.coordinator.data.measures.get(self.sensor_code)
        if measure:
            self._last_known_value = measure.value
            self._last_known_timestamp = measure.timestamp.isoformat()
            _LOGGER.debug(
                "Initialized sensor %s with value: %s",
                self._attr_unique_id,
                self._last_known_value,
            )


class OsmerLastUpdateSensor(
    SensorEntity,
):
    """Representation of an OSMER last update timestamp sensor."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self,
        coordinator: OsmerDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize sensor."""

        self.coordinator = coordinator
        self.entity_description = description

        station = coordinator.data.station
        self._attr_unique_id = f"osmer_{station.id}_last_update"

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
    def native_value(self) -> str | None:
        """Return last update timestamp."""

        if not self.coordinator.data or not self.coordinator.data.measures:
            return None

        # Trova il timestamp più recente tra tutte le misurazioni
        latest_timestamp = None
        for measure in self.coordinator.data.measures.values():
            if measure.timestamp and (
                latest_timestamp is None or measure.timestamp > latest_timestamp
            ):
                latest_timestamp = measure.timestamp

        return latest_timestamp.isoformat() if latest_timestamp else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        if not self.coordinator.data or not self.coordinator.data.measures:
            if self.coordinator.is_offline and self.coordinator.osmer_last_update_success:
                latest_timestamp = self.coordinator.osmer_last_update_success
                return {
                    "iso_format": latest_timestamp.isoformat(),
                    "datetime": latest_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "friendly": latest_timestamp.strftime("%d/%m/%Y %H:%M:%S"),
                    "is_offline": True,
                    "offline_since": latest_timestamp.isoformat(),
                }
            return {}

        latest_timestamp = None
        for measure in self.coordinator.data.measures.values():
            if measure.timestamp and (
                latest_timestamp is None or measure.timestamp > latest_timestamp
            ):
                latest_timestamp = measure.timestamp

        if latest_timestamp:
            return {
                "iso_format": latest_timestamp.isoformat(),
                "datetime": latest_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "friendly": latest_timestamp.strftime("%d/%m/%Y %H:%M:%S"),
                "is_offline": self.coordinator.is_offline,
            }
        return {}

    @property
    def state(self) -> str | None:
        """Return the state with offline indicator."""
        value = self.native_value
        if value and self.coordinator.is_offline:
            return f"{value} (offline)"
        return value
