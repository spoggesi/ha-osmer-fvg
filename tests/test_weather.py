"""Tests for OSMER weather entity."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.osmer_fvg.api.models import (
    Measure,
    OsmerForecastDay,
    Sensor,
    Station,
)
from custom_components.osmer_fvg.coordinator import (
    OsmerData,
    OsmerDataUpdateCoordinator,
)
from custom_components.osmer_fvg.weather import OsmerWeatherEntity


async def test_weather_entity_basic(
    hass: HomeAssistant,
) -> None:
    """Test basic weather entity properties."""

    station = Station(
        id=209,
        name="Zuiano",
        istat=93005,
        latitude=45.874009,
        longitude=12.713078,
        altitude=9,
        status="N",
    )

    sensor_t = Sensor(
        id=2,
        station_id=209,
        code="T",
        name="Temperatura aria",
        decimals=1,
        unit="°C",
        status="O",
    )

    sensor_u = Sensor(
        id=3,
        station_id=209,
        code="U",
        name="Umidità relativa",
        decimals=1,
        unit="%",
        status="O",
    )

    measure_t = Measure(
        station_id=209,
        sensor_id=2,
        timestamp=datetime.now(UTC),
        latitude=45.874009,
        longitude=12.713078,
        value=25.5,
    )

    measure_u = Measure(
        station_id=209,
        sensor_id=3,
        timestamp=datetime.now(UTC),
        latitude=45.874009,
        longitude=12.713078,
        value=65.0,
    )

    forecasts = [
        OsmerForecastDay(
            date="2024-08-11",
            condition="sunny",
            temp_min=20.0,
            temp_max=30.0,
            precipitation_probability=10,
            summary="Soleggiato",
        ),
        OsmerForecastDay(
            date="2024-08-12",
            condition="partlycloudy",
            temp_min=18.0,
            temp_max=28.0,
            precipitation_probability=20,
            summary="Parzialmente nuvoloso",
        ),
    ]

    coordinator = MagicMock(spec=OsmerDataUpdateCoordinator)
    coordinator.data = OsmerData(
        station=station,
        sensors={
            "T": sensor_t,
            "U": sensor_u,
        },
        measures={
            "T": measure_t,
            "U": measure_u,
        },
        forecasts=forecasts,
    )

    entity = OsmerWeatherEntity(coordinator)

    # Test basic properties
    assert entity.unique_id == "osmer_209_weather"
    assert entity.native_temperature_unit == UnitOfTemperature.CELSIUS
    assert entity.native_temperature == 25.5
    assert entity.humidity == 65.0

    # Test device info
    device_info = entity.device_info
    assert device_info["identifiers"] == {("osmer_fvg", "209")}
    assert device_info["name"] == "OSMER Zuiano"
    assert device_info["manufacturer"] == "OSMER FVG"
    assert device_info["model"] == "Weather Station"


async def test_weather_entity_with_rain(
    hass: HomeAssistant,
) -> None:
    """Test weather entity condition with rain."""

    station = Station(
        id=209,
        name="Zuiano",
        istat=93005,
        latitude=45.874009,
        longitude=12.713078,
        altitude=9,
        status="N",
    )

    sensor_prec = Sensor(
        id=4,
        station_id=209,
        code="Prec_5_min",
        name="Precipitazione ultimi 5 minuti",
        decimals=1,
        unit="mm",
        status="O",
    )

    measure_prec = Measure(
        station_id=209,
        sensor_id=4,
        timestamp=datetime.now(UTC),
        latitude=45.874009,
        longitude=12.713078,
        value=2.5,
    )

    coordinator = MagicMock(spec=OsmerDataUpdateCoordinator)
    coordinator.data = OsmerData(
        station=station,
        sensors={
            "Prec_5_min": sensor_prec,
        },
        measures={
            "Prec_5_min": measure_prec,
        },
        forecasts=[],
    )

    entity = OsmerWeatherEntity(coordinator)

    # Should be rainy when precipitation > 0
    assert entity.condition == "rainy"


async def test_weather_entity_forecast(
    hass: HomeAssistant,
) -> None:
    """Test weather entity forecast generation."""

    station = Station(
        id=209,
        name="Zuiano",
        istat=93005,
        latitude=45.874009,
        longitude=12.713078,
        altitude=9,
        status="N",
    )

    forecasts = [
        OsmerForecastDay(
            date="2024-08-11T12:00:00+00:00",
            condition="sunny",
            temp_min=20.0,
            temp_max=30.0,
            precipitation_probability=10,
            summary="Soleggiato",
        ),
        OsmerForecastDay(
            date="2024-08-12",
            condition="rainy",
            temp_min=18.0,
            temp_max=25.0,
            precipitation_probability=80,
            summary="Pioggia",
        ),
    ]

    coordinator = MagicMock(spec=OsmerDataUpdateCoordinator)
    coordinator.data = OsmerData(
        station=station,
        sensors={},
        measures={},
        forecasts=forecasts,
    )

    entity = OsmerWeatherEntity(coordinator)

    # Test forecast list
    forecast_list = entity.forecast
    assert len(forecast_list) == 2

    assert forecast_list[0]["datetime"] == "2024-08-11T12:00:00+00:00"
    assert forecast_list[0]["condition"] == "sunny"
    assert forecast_list[0]["native_temperature"] == 30.0
    assert forecast_list[0]["native_templow"] == 20.0
    assert forecast_list[0]["precipitation_probability"] == 10

    # Test async_forecast_daily
    daily_forecast = await entity.async_forecast_daily()
    assert len(daily_forecast) == 2

    # Test async_get_forecasts_response
    response = await entity.async_get_forecasts_response("daily")
    assert "daily" in response
    assert len(response["daily"]) == 2


async def test_weather_entity_without_data(
    hass: HomeAssistant,
) -> None:
    """Test weather entity with no data."""

    station = Station(
        id=209,
        name="Zuiano",
        istat=93005,
        latitude=45.874009,
        longitude=12.713078,
        altitude=9,
        status="N",
    )

    coordinator = MagicMock(spec=OsmerDataUpdateCoordinator)
    coordinator.data = OsmerData(
        station=station,
        sensors={},
        measures={},
        forecasts=[],
    )

    entity = OsmerWeatherEntity(coordinator)

    # Should return defaults
    assert entity.native_temperature is None
    assert entity.humidity is None
    assert entity.condition == "sunny"
    assert entity.forecast == []
