"""Sensor platform for OSMER FVG."""

from __future__ import annotations

import logging
from datetime import datetime
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
from .helpers.calculations import calculate_derived_sensors

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

    # Add derived sensors (if base sensors are available)
    # Check which derived sensors can be created based on available base sensors
    available_base_sensors = set(coordinator.data.sensors.keys())
    derived_sensors_to_create = []
    
    for sensor_code, config in MONITORED_SENSORS.items():
        if config.get("derived") and sensor_code not in coordinator.enabled_sensors:
            # Check if we have the required base sensors
            required_base = []
            if sensor_code == "DEW_POINT" or sensor_code == "HEAT_INDEX" or sensor_code == "ABS_HUMIDITY":
                required_base = ["T", "U"]
            elif sensor_code == "WIND_CHILL":
                required_base = ["T", "VV"]
            
            if all(base in available_base_sensors for base in required_base):
                derived_sensors_to_create.append(sensor_code)
    
    for sensor_code in derived_sensors_to_create:
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
            OsmerDerivedSensor(
                coordinator,
                sensor_code,
                description,
            )
        )

    # Add alerts sensor
    entities.append(
        OsmerAlertsSensor(
            coordinator,
        )
    )

    # Add health sensor for diagnostics
    entities.append(
        OsmerHealthSensor(
            coordinator,
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


class OsmerDerivedSensor(
    SensorEntity,
):
    """Representation of a derived OSMER sensor (calculated from base sensors)."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

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

        station = coordinator.data.station
        self._attr_unique_id = f"osmer_{station.id}_{sensor_code}"
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
        """Return calculated value for derived sensor."""

        if not self.coordinator.data or not self.coordinator.data.measures:
            if self.coordinator.is_offline and self._last_known_value is not None:
                return self._last_known_value
            return None

        derived_values = calculate_derived_sensors(
            self.coordinator.data.measures
        )
        
        value = derived_values.get(self.sensor_code)
        
        if value is not None:
            self._last_known_value = value
            self._last_known_timestamp = datetime.now().isoformat()
            return value
        
        if self.coordinator.is_offline and self._last_known_value is not None:
            return self._last_known_value
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        station = self.coordinator.data.station
        
        attrs: dict[str, Any] = {
            "station": station.name,
            "station_id": station.id,
            "sensor_code": self.sensor_code,
            "sensor_type": "derived",
            "last_known_value": self._last_known_value,
            "last_known_timestamp": self._last_known_timestamp,
            "is_offline": self.coordinator.is_offline,
            "offline_since": (
                self.coordinator.osmer_last_update_success.isoformat()
                if self.coordinator.is_offline and self.coordinator.osmer_last_update_success
                else None
            ),
        }
        
        if self.sensor_code in ["DEW_POINT", "HEAT_INDEX", "ABS_HUMIDITY"]:
            if "T" in self.coordinator.data.measures:
                attrs["base_temperature"] = self.coordinator.data.measures["T"].value
            if "U" in self.coordinator.data.measures:
                attrs["base_humidity"] = self.coordinator.data.measures["U"].value
        
        if self.sensor_code == "WIND_CHILL":
            if "T" in self.coordinator.data.measures:
                attrs["base_temperature"] = self.coordinator.data.measures["T"].value
            if "VV" in self.coordinator.data.measures:
                attrs["base_wind_speed"] = self.coordinator.data.measures["VV"].value
        
        return attrs

    async def async_added_to_hass(self) -> None:
        """Initialize last known value when entity is added."""
        await super().async_added_to_hass()
        
        if self.coordinator.data and self.coordinator.data.measures:
            derived_values = calculate_derived_sensors(
                self.coordinator.data.measures
            )
            value = derived_values.get(self.sensor_code)
            if value is not None:
                self._last_known_value = value
                self._last_known_timestamp = datetime.now().isoformat()


class OsmerAlertsSensor(
    SensorEntity,
):
    """Representation of OSMER alerts sensor."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(
        self,
        coordinator: OsmerDataUpdateCoordinator,
    ) -> None:
        """Initialize sensor."""

        self.coordinator = coordinator
        station = coordinator.data.station
        self._attr_unique_id = f"osmer_{station.id}_alerts"
        self._last_known_alerts: list[Any] = []

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
    def native_value(self) -> str:
        """Return the highest alert level or 'none'."""
        if not self.coordinator.data or not self.coordinator.data.alerts:
            return "none"
        
        # Update last known alerts
        self._last_known_alerts = self.coordinator.data.alerts
        
        # Determine highest alert level
        level_priority = {"green": 0, "yellow": 1, "orange": 2, "red": 3}
        max_level = "none"
        max_priority = -1
        
        for alert in self.coordinator.data.alerts:
            priority = level_priority.get(alert.level.lower(), -1)
            if priority > max_priority:
                max_priority = priority
                max_level = alert.level.lower()
        
        return max_level if max_level != "none" else "none"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {
                "active_alerts": 0,
                "last_known_alerts": self._last_known_alerts,
                "is_offline": self.coordinator.is_offline,
            }
        
        alerts = self.coordinator.data.alerts
        
        attrs: dict[str, Any] = {
            "active_alerts": len(alerts),
            "alerts": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "description": alert.description,
                    "level": alert.level,
                    "type": alert.type,
                    "start_time": alert.start_time.isoformat() if alert.start_time else None,
                    "end_time": alert.end_time.isoformat() if alert.end_time else None,
                    "zones": alert.zones,
                }
                for alert in alerts
            ],
            "last_known_alerts": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "level": alert.level,
                }
                for alert in self._last_known_alerts
            ],
            "is_offline": self.coordinator.is_offline,
            "offline_since": (
                self.coordinator.osmer_last_update_success.isoformat()
                if self.coordinator.is_offline and self.coordinator.osmer_last_update_success
                else None
            ),
        }
        
        return attrs

    @property
    def state(self) -> str:
        """Return the state with additional info."""
        value = self.native_value
        if value == "none":
            return "Nessuna allerta attiva"
        return f"Allerta {value.upper()}"


class OsmerHealthSensor(
    SensorEntity,
):
    """Representation of OSMER integration health sensor."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:heart-pulse"
    _attr_state_class = None

    def __init__(
        self,
        coordinator: OsmerDataUpdateCoordinator,
    ) -> None:
        """Initialize sensor."""

        self.coordinator = coordinator
        station = coordinator.data.station
        self._attr_unique_id = f"osmer_{station.id}_health"

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
    def native_value(self) -> str:
        """Return health status."""
        if self.coordinator.is_offline:
            return "offline"
        
        if not self.coordinator.data:
            return "initializing"
        
        if self.coordinator.data.station is None:
            return "error"
        
        return "ok"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed health information."""
        from .const import VERSION

        station = self.coordinator.data.station if self.coordinator.data else None
        
        attrs: dict[str, Any] = {
            "status": self.native_value,
            "version": VERSION,
            "is_offline": self.coordinator.is_offline,
            "last_update_success": (
                self.coordinator.osmer_last_update_success.isoformat()
                if self.coordinator.osmer_last_update_success
                else None
            ),
            "update_interval_seconds": self.coordinator.update_interval.total_seconds(),
        }
        
        if station:
            attrs["station_id"] = station.id
            attrs["station_name"] = station.name
            attrs["station_latitude"] = station.latitude
            attrs["station_longitude"] = station.longitude
            attrs["station_altitude"] = station.altitude
        
        if self.coordinator.data:
            attrs["sensors_count"] = len(self.coordinator.data.sensors)
            attrs["measures_count"] = len(self.coordinator.data.measures)
            attrs["forecasts_count"] = len(self.coordinator.data.forecasts)
            attrs["alerts_count"] = len(self.coordinator.data.alerts)
            
            # List of active sensors
            attrs["active_sensors"] = list(self.coordinator.data.sensors.keys())
            
            # List of sensors with data
            attrs["sensors_with_data"] = list(self.coordinator.data.measures.keys())
        
        # Options
        if self.coordinator._options:
            attrs["options"] = {
                "scan_interval": self.coordinator._options.get("scan_interval", 15),
                "retry_count": self.coordinator._options.get("retry_count", 3),
                "retry_delay": self.coordinator._options.get("retry_delay", 5),
                "timeout": self.coordinator._options.get("timeout", 30),
            }
        
        # Cache info
        attrs["cache"] = {
            "loaded": self.coordinator._cache_loaded,
            "version": self.coordinator._cache_data.get("version") if self.coordinator._cache_data else None,
        }
        
        return attrs

    @property
    def state(self) -> str:
        """Return state with friendly name."""
        value = self.native_value
        if value == "ok":
            return "✅ OK"
        elif value == "offline":
            return "⚠️ Offline"
        elif value == "initializing":
            return "⏳ Inizializzazione"
        else:
            return "❌ Errore"
