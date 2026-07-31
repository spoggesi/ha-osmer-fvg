"""The OSMER FVG integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)

from .api.client import OsmerApiClient
from .const import DOMAIN
from .coordinator import OsmerDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up OSMER FVG from a config entry."""

    session = async_get_clientsession(
        hass,
    )

    client = OsmerApiClient(
        session,
    )

    coordinator = OsmerDataUpdateCoordinator(
        hass,
        client,
        station_id=entry.data["station_id"],
        enabled_sensors=entry.data.get(
            "enabled_sensors",
        ),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(
        DOMAIN,
        {},
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload OSMER FVG entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:

        hass.data[DOMAIN].pop(
            entry.entry_id,
        )

    return unload_ok