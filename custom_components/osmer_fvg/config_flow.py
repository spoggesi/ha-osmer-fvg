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
    build_address_selector,
    build_nearest_station_selector,
    build_selection_method_selector,
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


    async def _initialize(self) -> bool:
        """Initialize services and load stations."""

        if self.loader is None:

            self.loader = FlowLoader(
                self.hass,
            )

            self.service = FlowService(
                self.hass,
                self.flow_context,
                self.loader,
            )

        if self.service is None:
            return False

        try:

            if not self.flow_context.stations:

                stations = await self.service.load_stations()

                if not stations:
                    return False

                await self.service.preload()

        except (
            OsmerConnectionError,
            OsmerApiResponseError,
        ) as err:

            _LOGGER.warning(
                "Unable to load OSMER data: %s",
                err,
            )

            return False

        return True


    async def _load_station_sensors(
        self,
        stations,
    ) -> None:
        """Load sensors only for required stations."""

        if self.loader is None:
            return

        for station in stations:

            if station.id in self.flow_context.sensor_cache:
                continue

            try:

                sensors = await self.loader.get_sensors(
                    station,
                )

                self.flow_context.sensor_cache[
                    station.id
                ] = sensors

            except (
                OsmerConnectionError,
                OsmerApiResponseError,
            ):

                self.flow_context.sensor_cache[
                    station.id
                ] = []


    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Select configuration method."""

        if not await self._initialize():

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
        """Select station manually."""

        if self.service is None:
            return self.async_abort(
                reason="cannot_connect",
            )

        stations = self.flow_context.stations

        await self._load_station_sensors(
            stations,
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
            step_id="station",
            data_schema=build_station_selector(
                stations,
                self.flow_context.sensor_cache,
            ),
        )


    async def async_step_address(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Search station by address."""

        if self.service is None:

            return self.async_abort(
                reason="cannot_connect",
            )


        if user_input is not None:

            address = user_input.get(
                "address",
                "",
            ).strip()


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


            nearest = self.service.nearest_stations(
                limit=5,
            )


            await self._load_station_sensors(
                nearest,
            )


            return await self.async_step_nearest()


        return self.async_show_form(
            step_id="address",
            data_schema=build_address_selector(),
        )


    async def async_step_nearest(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Select nearest station."""

        if self.service is None:
            return self.async_abort(
                reason="cannot_connect",
            )


        stations = self.flow_context.nearest


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
            step_id="nearest",
            data_schema=build_nearest_station_selector(
                stations,
                self.flow_context.sensor_cache,
                self.flow_context.latitude,
                self.flow_context.longitude,
            ),
        )


    async def async_step_sensors(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Select sensors."""

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