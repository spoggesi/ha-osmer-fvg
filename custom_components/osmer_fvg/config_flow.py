"""Config flow for the OSMER FVG integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .flow.confirm import (
    build_description_placeholders,
)
from .flow.context import FlowContext
from .flow.entry import (
    build_entry_data,
    build_entry_title,
)
from .flow.loader import FlowLoader
from .flow.selectors import (
    build_sensor_selector,
    build_station_selector,
)
from .flow.service import FlowService


class OsmerFVGConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle an OSMER FVG config flow."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""

        self._context = FlowContext()

        self._loader: FlowLoader | None = None

        self._service: FlowService | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Choose the weather station."""

        if self._loader is None:
            self._loader = FlowLoader(
                self.hass,
            )

        if self._service is None:
            self._service = FlowService(
                self.hass,
                self._context,
            )

        if user_input is not None:

            station_id = int(
                user_input["station"],
            )

            station = await self._loader.get_station(
                station_id,
            )

            if station is None:

                return self.async_abort(
                    reason="invalid_station",
                )

            self._context.station = station

            await self.async_set_unique_id(
                f"osmer_station_{station.id}",
            )

            self._abort_if_unique_id_configured()

            sensors = await self._service.load_sensors(
                station,
            )

            self._context.sensors = sensors

            return self.async_show_form(
                step_id="sensors",
                data_schema=build_sensor_selector(
                    sensors,
                ),
            )

        stations = await self._service.load_stations()

        await self._service.preload()

        station_sensors = {
            station.id: await self._loader.get_sensors(
                station,
            )
            for station in stations
        }

        return self.async_show_form(
            step_id="user",
            data_schema=build_station_selector(
                stations,
                station_sensors,
            ),
        )

    async def async_step_sensors(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Choose sensors to enable."""

        if user_input is None:

            return self.async_abort(
                reason="missing_sensor_selection",
            )

        self._context.enabled_sensors = (
            user_input.get(
                "enabled_sensors",
                [],
            )
        )

        if self._context.station is None:

            return self.async_abort(
                reason="missing_station",
            )

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders=(
                build_description_placeholders(
                    self._context.station,
                    self._context.sensors,
                )
            ),
        )

    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm configuration."""

        if self._context.station is None:

            return self.async_abort(
                reason="missing_station",
            )

        if user_input is None:

            return self.async_show_form(
                step_id="confirm",
                data_schema=vol.Schema({}),
                description_placeholders=(
                    build_description_placeholders(
                        self._context.station,
                        self._context.sensors,
                    )
                ),
            )

        entry_data = build_entry_data(
            station=self._context.station,
            enabled_sensors=self._context.enabled_sensors,
        )

        return self.async_create_entry(
            title=build_entry_title(
                self._context.station,
            ),
            data=entry_data,
        )

    async def async_step_import(
        self,
        import_info: dict[str, Any],
    ) -> FlowResult:
        """Handle import from configuration.yaml."""

        station_id = import_info.get(
            "station_id",
        )

        if station_id is None:

            return self.async_abort(
                reason="invalid_import",
            )

        await self.async_set_unique_id(
            f"osmer_station_{station_id}",
        )

        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="OSMER FVG",
            data=import_info,
        )