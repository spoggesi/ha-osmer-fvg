"""Weather platform for OSMER FVG."""

from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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


class OsmerWeatherEntity(CoordinatorEntity[OsmerDataUpdateCoordinator], WeatherEntity):
    """Representation of an OSMER weather entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfLength.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator: OsmerDataUpdateCoordinator) -> None:
        """Initialize weather entity."""

        super().__init__(coordinator)
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
            sw_version="0.3.2",
        )

    @property
    def native_temperature(self) -> float | None:
        """Return current temperature."""

        if not self.coordinator.data or not self.coordinator.data.measures:
            return None

        measure = self.coordinator.data.measures.get("T")
        return measure.value if measure else None

    @property
    def humidity(self) -> float | None:
        """Return current humidity."""

        if not self.coordinator.data or not self.coordinator.data.measures:
            return None

        measure = self.coordinator.data.measures.get("U")
        return measure.value if measure else None

    @property
    def condition(self) -> str | None:
        """Return current weather condition based on rain sensor or forecast."""

        if not self.coordinator.data or not self.coordinator.data.measures:
            return "sunny"

        rain_measure = self.coordinator.data.measures.get(
            "Prec_5_min"
        ) or self.coordinator.data.measures.get("RR")

        if rain_measure and rain_measure.value is not None and rain_measure.value > 0:
            return "rainy"

        if self.coordinator.data.forecasts:
            return self.coordinator.data.forecasts[0].condition or "sunny"

        return "sunny"

    def _get_forecast_list(self) -> list[Forecast]:
        """Build forecast items list safely formatted for HA Frontend."""

        if not self.coordinator.data or not self.coordinator.data.forecasts:
            return []

        forecast_list: list[Forecast] = []
        current_temp = self.native_temperature or 20.0

        for item_f in self.coordinator.data.forecasts:
            date_str = item_f.date
            if "T" not in date_str:
                date_str = f"{date_str}T12:00:00+00:00"

            max_temp = item_f.temp_max if item_f.temp_max is not None else current_temp
            min_temp = (
                item_f.temp_min if item_f.temp_min is not None else (current_temp - 4.0)
            )

            forecast_item: Forecast = {
                "datetime": date_str,
                "condition": item_f.condition or "sunny",
                "native_temperature": float(max_temp),
                "native_templow": float(min_temp),
            }

            if item_f.precipitation_probability is not None:
                forecast_item["precipitation_probability"] = (
                    item_f.precipitation_probability
                )

            forecast_list.append(forecast_item)

        return forecast_list

    @property
    def forecast(self) -> list[Forecast] | None:
        """Return daily forecast list for legacy weather cards."""

        return self._get_forecast_list()

    async def async_forecast_daily(self) -> list[Forecast]:
        """Return daily forecast (legacy service)."""

        return self._get_forecast_list()

    async def async_get_forecasts_response(
        self, forecast_type: str
    ) -> dict[str, list[Forecast]]:
        """Return forecast response for HA 2024+ UI weather card."""

        if forecast_type == "daily":
            return {"daily": self._get_forecast_list()}

        return {forecast_type: []}
