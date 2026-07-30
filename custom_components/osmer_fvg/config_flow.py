"""Config flow for OSMER FVG integration."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientSession
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import OsmerApiClient
from .api.models import Station
from .const import DOMAIN


class OsmerFVGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OSMER FVG."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._stations: list[Station] = []

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle user step."""

        if user_input is not None:
            return self.async_create_entry(
                title=user_input["station"],
                data=user_input,
            )

        stations = await self._async_get_stations()

        if not stations:
            return self.async_abort(
                reason="cannot_connect"
            )

        self._stations = stations

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(stations),
        )

    async def _async_get_stations(self) -> list[Station]:
        """Fetch available stations."""

        session: ClientSession = async_get_clientsession(self.hass)

        client = OsmerApiClient(session)

        return await client.get_stations()

    @staticmethod
    def _get_schema(
        stations: list[Station],
    ):
        """Create station selector schema."""

        import voluptuous as vol

        return vol.Schema(
            {
                vol.Required("station"): vol.In(
                    {
                        station.id: station.name
                        for station in stations
                    }
                )
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ):
        """Return options flow."""

        return