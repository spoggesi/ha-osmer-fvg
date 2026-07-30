"""Tests for the OSMER coordinator."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant

from custom_components.osmer_fvg.api.models import (
    Measure,
    Sensor,
    Station,
)
from custom_components.osmer_fvg.coordinator import (
    OsmerDataUpdateCoordinator,
)


async def test_coordinator_update(
    hass: HomeAssistant,
) -> None:
    """Test coordinator retrieves weather data."""

    client = MagicMock()

    client.get_station = AsyncMock(
        return_value=Station(
            id=51,
            name="Dignano",
            istat=30032,
            latitude=46.084672,
            longitude=12.930306,
            altitude=112,
            status="N",
        )
    )

    client.get_sensors = AsyncMock(
        return_value=[
            Sensor(
                id=2,
                station_id=51,
                code="T",
                name="Temperatura aria",
                decimals=1,
                unit="°C",
                status="O",
            )
        ]
    )

    client.get_measures = AsyncMock(
        return_value=[
            Measure(
                station_id=51,
                sensor_id=2,
                timestamp=None,
                latitude=46.084672,
                longitude=12.930306,
                value=25.5,
            )
        ]
    )

    coordinator = OsmerDataUpdateCoordinator(
        hass,
        client,
        station_id=51,
    )

    await coordinator.async_refresh()

    assert coordinator.data is not None

    assert coordinator.data.station.name == ("Dignano")

    assert "T" in coordinator.data.sensors

    assert coordinator.data.measures["T"].value == 25.5
