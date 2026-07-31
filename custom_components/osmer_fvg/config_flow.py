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

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle station selection method."""

        if self.loader is None:
            self.loader = FlowLoader(
                self.hass,
            )

            self.service = FlowService(
                self.hass,
                self.flow_context,
                self.loader,
            )

        if self.service is None or self.loader is None:
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
            selection_method = user_input.get(
                "selection_method",
            )

            if selection_method == "distance":
                return await self.async_step_address()

            if selection_method == "station":
                return await self.async_step_station()

        return self.async_show_form(
            step_id="user",
            data_schema=build_selection_method_selector(),
        )

    async def async_step_station(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle direct station selection."""

        if self.service is None:
            return self.async_abort(
                reason="cannot_connect",
            )

        stations = self.flow_context.stations

        station_sensors = (
            self.flow_context.sensor_cache
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
                str(station.id),
            )

            self._abort_if_unique_id_configured()

            self.flow_context.station = station

            return await self.async_step_sensors()

        return self.async_show_form(
            step_id="station",
            data_schema=build_station_selector(
                stations,
                station_sensors,
            ),
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
            address = user_input.get(
                "address",
                "",
            ).strip()

            if not address:
                return self.async_show_form(
                    step_id="address",
                    data_schema=build_address_selector(),
                    errors={
                        "address": "invalid_address",
                    },
                )

            try:
                result = await self.service.search_address(
                    address,
                )

            except (
                OsmerConnectionError,
                OsmerApiResponseError,
            ) as err:
                _LOGGER.warning(
                    "Unable to geocode address: %s",
                    err,
                )

                return self.async_show_form(
                    step_id="address",
                    data_schema=build_address_selector(),
                    errors={
                        "base": "cannot_connect",
                    },
                )

            if result is None:
                return self.async_show_form(
                    step_id="address",
                    data_schema=build_address_selector(),
                    errors={
                        "address": "address_not_found",
                    },
                )

            nearest = self.service.nearest_stations(
                limit=5,
            )

            if not nearest:
                return self.async_abort(
                    reason="no_nearby_stations",
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
        """Handle nearest station selection."""

        if self.service is None:
            return self.async_abort(
                reason="cannot_connect",
            )

        latitude = self.flow_context.latitude
        longitude = self.flow_context.longitude

        if latitude is None or longitude is None:
            return self.async_abort(
                reason="missing_coordinates",
            )

        nearest = self.flow_context.nearest

        if not nearest:
            nearest = self.service.nearest_stations(
                limit=5,
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
                str(station.id),
            )

            self._abort_if_unique_id_configured()

            self.flow_context.station = station

            return await self.async_step_sensors()

        return self.async_show_form(
            step_id="nearest",
            data_schema=build_nearest_station_selector(
                nearest,
                self.flow_context.sensor_cache,
                latitude,
                longitude,
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

        if self.service is None:
            return self.async_abort(
                reason="cannot_connect",
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