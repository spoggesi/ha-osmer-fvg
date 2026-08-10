"""Tests for OSMER weather entity."""

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.osmer_fvg.api.models import Measure, Station
from custom_components.osmer_fvg.coordinator import OsmerData
from custom_components.osmer_fvg.weather import OsmerWeatherEntity


async def test_weather_entity_properties(hass: HomeAssistant) -> None:
    """Test weather entity values."""
    station = Station(
        id=209,
        name="Zuiano",
        istat=93005,
        latitude=45.874009,
        longitude=12.713078,
        altitude=9,
        status="N",
    )

    t_measure = Measure(
        station_id=209,
        sensor_id=2,
        timestamp=None,
        latitude=45.874009,
        longitude=12.713078,
        value=22.5,
    )

    u_measure = Measure(
        station_id=209,
        sensor_id=3,
        timestamp=None,
        latitude=45.874009,
        longitude=12.713078,
        value=65.0,
    )

    coordinator = MagicMock()
    coordinator.data = OsmerData(
        station=station,
        sensors={},
        measures={"T": t_measure, "U": u_measure},
    )

    weather = OsmerWeatherEntity(coordinator)

    assert weather.native_temperature == 22.5
    assert weather.humidity == 65.0
    assert weather.unique_id == "osmer_209_weather"
