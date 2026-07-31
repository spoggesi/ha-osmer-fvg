"""Config flow for OSMER FVG integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
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
    build_address_selector,
    build_back_selector,
    build_nearest_station_selector,
    build_selection_method_selector,
    build_sensor_selector,
    build_station_selector,
)
from .flow.service import FlowService

_LOGGER = logging.getLogger(__name__)

BACK_OPTION = "__back__"


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



    async def _async_init_services(
        self,
    ) -> None:
        """Initialize services."""

        if self.loader is None:

            self.loader = FlowLoader(
                self.hass,
            )


            self.service = FlowService(
                self.hass,
                self.flow_context,
                self.loader,
            )


            await self.service.async_init_cache()



    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle initial selection."""

        await self._async_init_services()


        if self.service is None:

            return self.async_abort(
                reason="cannot_connect",
            )



        try:

            if not self.flow_context.stations:

                stations = await self.service.load_stations()


                if not stations:

                    return self.async_abort(
                        reason="invalid_station",
                    )


                await self.service.preload()



        except (
            OsmerConnectionError,
            OsmerApiResponseError,
        ) as err:

            _LOGGER.warning(
                "Unable to load OSMER data: %s",
                err,
            )


            return self.async_abort(
                reason="cannot_connect",
            )



        if user_input is not None:

            method = user_input.get(
                "selection_method",
            )


            if method == "station":

                return await self.async_step_station()


            if method == "address":

                return await self.async_step_address()



        return self.async_show_form(
            step_id="user",
            data_schema=build_selection_method_selector(),
        )



    async def async_step_station(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle station selection."""


        if self.service is None:

            return self.async_abort(
                reason="cannot_connect",
            )



        if user_input is not None:


            if user_input.get(
                "action",
            ) == BACK_OPTION:

                return await self.async_step_user()



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



        schema = build_station_selector(
            self.flow_context.stations,
            self.flow_context.sensor_cache,
        )



        schema = schema.extend(
            {
                vol.Optional(
                    "action",
                ): build_back_selector(),
            }
        )



        return self.async_show_form(
            step_id="station",
            data_schema=schema,
        )



    async def async_step_address(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle address search."""


        if self.service is None:

            return self.async_abort(
                reason="cannot_connect",
            )



        if user_input is not None:


            if user_input.get(
                "action",
            ) == BACK_OPTION:

                return await self.async_step_user()



            address = user_input.get(
                "address",
                "",
            ).strip()



            if not address:

                return self.async_show_form(
                    step_id="address",
                    data_schema=build_address_selector(),
                    errors={
                        "base": "invalid_address",
                    },
                )



            result = await self.service.search_address(
                address,
            )



            if result is None:

                return self.async_show_form(
                    step_id="address",
                    data_schema=build_address_selector(),
                    errors={
                        "base": "address_not_found",
                    },
                )



            self.flow_context.nearest = (
                self.service.nearest_stations(
                    limit=5,
                )
            )



            return await self.async_step_nearest()



        schema = build_address_selector()



        schema = schema.extend(
            {
                vol.Optional(
                    "action",
                ): build_back_selector(),
            }
        )



        return self.async_show_form(
            step_id="address",
            data_schema=schema,
        )



    async def async_step_nearest(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle nearest stations."""

        if self.service is None:

            return self.async_abort(
                reason="cannot_connect",
            )



        if user_input is not None:


            if user_input.get(
                "action",
            ) == BACK_OPTION:

                return await self.async_step_address()



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



        schema = build_nearest_station_selector(
            self.flow_context.nearest,
            self.flow_context.sensor_cache,
            self.flow_context.latitude,
            self.flow_context.longitude,
        )



        schema = schema.extend(
            {
                vol.Optional(
                    "action",
                ): build_back_selector(),
            }
        )



        return self.async_show_form(
            step_id="nearest",
            data_schema=schema,
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



        if self.service is None:

            return self.async_abort(
                reason="cannot_connect",
            )



        sensors = await self.service.load_sensors(
            self.flow_context.station,
        )



        if user_input is not None:


            if user_input.get(
                "action",
            ) == BACK_OPTION:

                return await self.async_step_station()



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



        schema = build_sensor_selector(
            sensors,
        )



        schema = schema.extend(
            {
                vol.Optional(
                    "action",
                ): build_back_selector(),
            }
        )



        return self.async_show_form(
            step_id="sensors",
            data_schema=schema,
        )



    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm configuration."""


        station = self.flow_context.station



        if station is None:

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


            if user_input.get(
                "action",
            ) == BACK_OPTION:

                return await self.async_step_sensors()



            return self.async_create_entry(
                title=build_entry_title(
                    station,
                ),
                data=build_entry_data(
                    station,
                    self.flow_context.enabled_sensors,
                ),
            )



        schema = vol.Schema(
            {
                vol.Optional(
                    "action",
                ): build_back_selector(),
            }
        )



        return self.async_show_form(
            step_id="confirm",
            data_schema=schema,
            description_placeholders=build_description_placeholders(
                station,
                selected_sensors,
            ),
        )