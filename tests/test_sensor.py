"""Tests for OSMER sensors."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.osmer_fvg.api.models import (
    Measure,
    Sensor,
    Station,
)
from custom_components.osmer_fvg.coordinator import (
    OsmerData,
)
from custom_components.osmer_fvg.sensor import (
    OsmerSensor,
)


async def test_sensor_value(
    hass: HomeAssistant,
) -> None:
    """Test sensor returns latest value."""

    station = Station(
        id=209,
        name="Zuiano",
        istat=93005,
        latitude=45.874009,
        longitude=12.713078,
        altitude=9,
        status="N",
    )


    sensor = Sensor(
        id=2,
        station_id=209,
        code="T",
        name="Temperatura aria",
        decimals=1,
        unit="°C",
        status="O",
    )


    measure = Measure(
        station_id=209,
        sensor_id=2,
        timestamp=datetime.now(
            timezone.utc
        ),
        latitude=45.874009,
        longitude=12.713078,
        value=35.2,
    )


    coordinator = MagicMock()

    coordinator.data = OsmerData(
        station=station,
        sensors={
            "T": sensor,
        },
        measures={
            "T": measure,
        },
    )


    entity = OsmerSensor(
        coordinator,
        "T",
    )


    assert entity.native_value == 35.2

    assert entity.unique_id == (
        "osmer_209_T"
    )

    assert entity.extra_state_attributes[
        "station"
    ] == "Zuiano"