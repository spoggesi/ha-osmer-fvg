"""Data coordinator for the OSMER FVG integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.client import OsmerApiClient
from .api.models import Station
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN


_LOGGER = logging.getLogger(__name__)


class OsmerDataUpdateCoordinator(DataUpdateCoordinator[list[Station]]):
    """Coordinator to fetch OSMER weather station data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: OsmerApiClient,
    ) -> None:
        """Initialize the coordinator."""

        self.client = client

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=DEFAULT_SCAN_INTERVAL
            ),
        )

    async def _async_update_data(self) -> list[Station]:
        """Fetch data from OSMER API."""

        try:
            return await self.client.get_stations()

        except Exception as err:
            raise UpdateFailed(
                f"Unable to fetch OSMER data: {err}"
            ) from err