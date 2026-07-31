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

    entities: list[SensorEntity] = []

    for sensor_code in coordinator.data.sensors:
        if sensor_code not in MONITORED_SENSORS:
            continue

        entities.append(
            OsmerSensor(
                coordinator,
                sensor_code,
            )
        )

    async_add_entities(
        entities,
    )


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
        sensor_config = MONITORED_SENSORS[sensor_code]

        self._attr_unique_id = (
            f"osmer_{station.id}_{sensor.code}"
        )

        self._attr_name = sensor_config["name"]

        self._attr_native_unit_of_measurement = (
            sensor_config["unit"]
        )

        self._attr_device_class = (
            self._get_device_class(
                sensor_code,
            )
        )

        self._attr_state_class = (
            SensorStateClass.MEASUREMENT
        )

        self._attr_icon = (
            self._get_icon(
                sensor_code,
            )
        )

    @property
    def device_info(
        self,
    ) -> DeviceInfo:
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
            configuration_url=(
                "https://monitor.protezionecivile.fvg.it"
            ),
            sw_version="0.1.3",
        )

    @property
    def native_value(
        self,
    ) -> float | None:
        """Return sensor value."""

        measure = (
            self.coordinator.data.measures.get(
                self.sensor_code,
            )
        )

        if measure is None:
            return None

        return measure.value

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return extra state attributes."""

        station = self.coordinator.data.station
        sensor = self.coordinator.data.sensors[
            self.sensor_code
        ]

        measure = (
            self.coordinator.data.measures.get(
                self.sensor_code,
            )
        )

        return {
            "station": station.name,
            "station_id": station.id,
            "sensor_code": sensor.code,
            "sensor_name": sensor.name,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "altitude": station.altitude,
            "last_update": (
                measure.timestamp.isoformat()
                if measure
                else None
            ),
        }

    @staticmethod
    def _get_device_class(
        code: str,
    ) -> SensorDeviceClass | None:
        """Return Home Assistant device class."""

        mapping = {
            "T": SensorDeviceClass.TEMPERATURE,
            "U": SensorDeviceClass.HUMIDITY,
            "RR": SensorDeviceClass.PRECIPITATION,
            "P": SensorDeviceClass.PRECIPITATION,
            "P_1h": SensorDeviceClass.PRECIPITATION,
            "Prec_5_min": SensorDeviceClass.PRECIPITATION,
            "Prec_60_min": SensorDeviceClass.PRECIPITATION,
            "Prec_3_ore": SensorDeviceClass.PRECIPITATION,
            "Prec_6_ore": SensorDeviceClass.PRECIPITATION,
            "Prec_12_ore": SensorDeviceClass.PRECIPITATION,
            "Prec_24_ore": SensorDeviceClass.PRECIPITATION,
            "Prec_48_ore": SensorDeviceClass.PRECIPITATION,
        }

        return mapping.get(code)

    @staticmethod
    def _get_icon(
        code: str,
    ) -> str:
        """Return sensor icon."""

        mapping = {
            "T": "mdi:thermometer",
            "U": "mdi:water-percent",
            "IDRO": "mdi:waves",
            "RR": "mdi:weather-rainy",
            "P": "mdi:weather-rainy",
            "P_1h": "mdi:weather-rainy",
            "Prec_5_min": "mdi:weather-rainy",
            "Prec_60_min": "mdi:weather-rainy",
            "Prec_3_ore": "mdi:weather-rainy",
            "Prec_6_ore": "mdi:weather-rainy",
            "Prec_12_ore": "mdi:weather-rainy",
            "Prec_24_ore": "mdi:weather-rainy",
            "Prec_48_ore": "mdi:weather-rainy",
            "CAR": "mdi:battery-charging",
            "SCAR": "mdi:battery-minus",
            "STSpluv (RAW)": "mdi:information-outline",
        }

        return mapping.get(
            code,
            "mdi:weather-partly-cloudy",
        )