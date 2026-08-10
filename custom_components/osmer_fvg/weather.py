"""Weather platform for OSMER FVG."""

from __future__ import annotations

from homeassistant.components.weather import (
    WeatherEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import OsmerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OSMER weather entity."""

    coordinator: OsmerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([OsmerWeatherEntity(coordinator)])


class OsmerWeatherEntity(WeatherEntity):
    """Representation of an OSMER weather entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfLength.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator: OsmerDataUpdateCoordinator) -> None:
        """Initialize weather entity."""
        self.coordinator = coordinator
        station = coordinator.data.station
        self._attr_unique_id = f"osmer_{station.id}_weather"

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
            sw_version="0.3.0",
        )

    @property
    def native_temperature(self) -> float | None:
        """Return current temperature."""
        measure = self.coordinator.data.measures.get("T")
        return measure.value if measure else None

    @property
    def humidity(self) -> float | None:
        """Return current humidity."""
        measure = self.coordinator.data.measures.get("U")
        return measure.value if measure else None

    @property
    def condition(self) -> str | None:
        """Return current weather condition based on rain sensor."""
        rain_measure = self.coordinator.data.measures.get(
            "Prec_5_min"
        ) or self.coordinator.data.measures.get("RR")

        if rain_measure and rain_measure.value is not None and rain_measure.value > 0:
            return "rainy"

        return "sunny"
