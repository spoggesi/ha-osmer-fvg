"""Tests for the OSMER coordinator."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant

from custom_components.osmer_fvg.api.models import Station
from custom_components.osmer_fvg.coordinator import (
    OsmerDataUpdateCoordinator,
)


async def test_coordinator_update(
    hass: HomeAssistant,
) -> None:
    """Test coordinator retrieves station data."""

    client = MagicMock()

    client.get_stations = AsyncMock(
        return_value=[
            Station(
                id=51,
                name="Dignano",
                istat=30032,
                latitude=46.084672,
                longitude=12.930306,
                altitude=112,
                status="N",
            )
        ]
    )

    coordinator = OsmerDataUpdateCoordinator(
        hass,
        client,
    )

    await coordinator.async_refresh()

    assert coordinator.data is not None
    assert len(coordinator.data) == 1
    assert coordinator.data[0].name == "Dignano"