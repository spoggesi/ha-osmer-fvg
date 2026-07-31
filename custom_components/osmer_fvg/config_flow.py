"""Config flow for OSMER FVG integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .api.exceptions import (
    OsmerApiResponseError,
    OsmerConnectionError,
)
from .const import DOMAIN
from .flow.confirm import build_description_placeholders
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

_LOGGER = logging.getLogger(__name__)


class OsmerFvgConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle OSMER FVG config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""

        self.flow_context = FlowContext()

        self.loader: FlowLoader | None = None
        self.service: FlowService | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle station selection."""

        if self.loader is None:

            self.loader = FlowLoader(
                self.hass,
            )

            self.service = FlowService(
                self.hass,
                self.flow_context,
                self.loader,
            )

        try:

            stations = await self.service.load_stations()

        except (
            OsmerConnectionError,
            OsmerApiResponseError,
        ) as err:

            _LOGGER.warning(
                "Unable to load OSMER stations: %s",
                err,
            )

            return self.async_abort(
                reason="cannot_connect",
            )

        if not stations:

            return self.async_abort(
                reason="invalid_station",
            )

        station_sensors: dict[int, Any] = {}

        try:

            await self.service.preload()

            for station in stations:

                station_sensors[station.id] = (
                    await self.loader.get_sensors(
                        station,
                    )
                )

        except (
            OsmerConnectionError,
            OsmerApiResponseError,
        ) as err:

            _LOGGER.warning(
                "Unable to preload sensors: %s",
                err,
            )

        if user_input is not None:

            station_id = int(
                user_input["station"],
            )

            station = await self.service.load_station(
                station_id,
            )

            if station is None:

                return self.async_abort(
                    reason="invalid_station",
                )

            await self.async_set_unique_id(
                str(
                    station.id,
                )
            )

            self._abort_if_unique_id_configured()

            self.flow_context.station = station

            return await self.async_step_sensors()

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
    ) -> ConfigFlowResult:
        """Handle sensor selection."""

        if self.flow_context.station is None:

            return self.async_abort(
                reason="missing_station",
            )

        try:

            sensors = await self.service.load_sensors(
                self.flow_context.station,
            )

        except (
            OsmerConnectionError,
            OsmerApiResponseError,
        ) as err:

            _LOGGER.warning(
                "Unable to load sensors: %s",
                err,
            )

            return self.async_abort(
                reason="cannot_connect",
            )

        if user_input is not None:

            enabled = user_input.get(
                "enabled_sensors",
                [],
            )

            if not enabled:

                return self.async_abort(
                    reason="missing_sensor_selection",
                )

            self.flow_context.enabled_sensors = enabled

            return await self.async_step_confirm()

        return self.async_show_form(
            step_id="sensors",
            data_schema=build_sensor_selector(
                sensors,
            ),
        )

    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm configuration."""

        if self.flow_context.station is None:

            return self.async_abort(
                reason="missing_station",
            )

        selected_sensors = [
            sensor
            for sensor in self.flow_context.sensors
            if sensor.code
            in self.flow_context.enabled_sensors
        ]

        if user_input is not None:

            station = self.flow_context.station

            return self.async_create_entry(
                title=build_entry_title(
                    station,
                ),
                data=build_entry_data(
                    station,
                    self.flow_context.enabled_sensors,
                ),
            )

        return self.async_show_form(
            step_id="confirm",
            description_placeholders=build_description_placeholders(
                self.flow_context.station,
                selected_sensors,
            ),
        )