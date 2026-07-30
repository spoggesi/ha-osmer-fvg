"""Config flow for OSMER FVG integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)

from .api.client import OsmerApiClient
from .api.exceptions import (
    OsmerApiResponseError,
    OsmerConnectionError,
)
from .api.models import Station
from .const import DOMAIN


class OsmerFVGConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle OSMER FVG config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""

        self._stations: list[Station] = []

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle user setup."""

        if user_input is not None:
            station_id = user_input["station_id"]

            station = next(
                (
                    item
                    for item in self._stations
                    if item.id == station_id
                ),
                None,
            )

            if station is None:
                return self.async_abort(
                    reason="invalid_station",
                )

            await self.async_set_unique_id(
                f"osmer_station_{station.id}",
            )

            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"OSMER {station.name}",
                data={
                    "station_id": station.id,
                    "station_name": station.name,
                },
            )

        try:
            stations = await self._async_get_stations()

        except (
            OsmerConnectionError,
            OsmerApiResponseError,
        ):
            return self.async_abort(
                reason="cannot_connect",
            )

        if not stations:
            return self.async_abort(
                reason="no_stations",
            )

        self._stations = stations

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(
                stations,
            ),
        )

    async def _async_get_stations(
        self,
    ) -> list[Station]:
        """Fetch available stations."""

        session = async_get_clientsession(
            self.hass,
        )

        client = OsmerApiClient(
            session,
        )

        return await client.get_stations()

    @staticmethod
    def _get_schema(
        stations: list[Station],
    ) -> vol.Schema:
        """Create station selector."""

        stations = sorted(
            stations,
            key=lambda station: station.name.casefold(),
        )

        return vol.Schema(
            {
                vol.Required(
                    "station_id",
                ): vol.In(
                    {
                        station.id: (
                            f"{station.name} ({station.id})"
                        )
                        for station in stations
                    }
                )
            }
        )