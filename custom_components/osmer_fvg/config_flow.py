"""Config flow for OSMER FVG integration."""

from __future__ import annotations

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback

from .api.exceptions import (
    OsmerApiResponseError,
    OsmerConnectionError,
)
from .const import (
    CONF_MULTI_STATION,
    CONF_OFFLINE_THRESHOLD,
    CONF_RETRY_COUNT,
    CONF_RETRY_DELAY,
    CONF_SCAN_INTERVAL,
    CONF_STATION_IDS,
    CONF_TIMEOUT,
    DEFAULT_OFFLINE_THRESHOLD,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MONITORED_SENSORS,
)
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
    build_station_search_selector,
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create options flow handler."""
        return OsmerFvgOptionsFlowHandler()

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
            
            if method == "multi_station":
                return await self.async_step_multi_station()

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
            if user_input.get("action") == BACK_OPTION:
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

    async def async_step_multi_station(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle multi-station selection."""

        if self.service is None:
            return self.async_abort(
                reason="cannot_connect",
            )

        if user_input is not None:
            if user_input.get("action") == BACK_OPTION:
                return await self.async_step_user()

            station_ids = user_input.get(CONF_STATION_IDS, [])
            
            if not station_ids:
                return self.async_show_form(
                    step_id="multi_station",
                    data_schema=build_station_search_selector(
                        self.flow_context.stations,
                        self.flow_context.sensor_cache,
                    ),
                    errors={
                        "base": "select_at_least_one_station",
                    },
                )

            # Load all selected stations
            selected_stations = []
            for station_id_str in station_ids:
                station_id = int(station_id_str)
                station = await self.service.load_station(station_id)
                if station:
                    selected_stations.append(station)

            if not selected_stations:
                return self.async_abort(
                    reason="invalid_stations",
                )

            # For multi-station, use a composite unique ID
            station_id_hash = hash(tuple(sorted(station_ids)))
            await self.async_set_unique_id(
                f"multi_{station_id_hash}",
            )

            self._abort_if_unique_id_configured()

            self.flow_context.stations = selected_stations
            self.flow_context.multi_station_mode = True

            # Load sensors for first station (we'll use the same for all in multi-mode)
            if selected_stations:
                sensors = await self.service.load_sensors(selected_stations[0])
                self.flow_context.sensors = sensors

            return await self.async_step_sensors()

        schema = build_station_search_selector(
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
            step_id="multi_station",
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
            if user_input.get("action") == BACK_OPTION:
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

            self.flow_context.nearest = self.service.nearest_stations(
                limit=5,
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
            if user_input.get("action") == BACK_OPTION:
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
            if user_input.get("action") == BACK_OPTION:
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

        station = self.flow_context.station
        multi_station = getattr(self.flow_context, 'multi_station_mode', False)
        
        selected_sensors = [
            sensor
            for sensor in self.flow_context.sensors
            if sensor.code in self.flow_context.enabled_sensors
        ]

        if user_input is not None:
            if user_input.get("action") == BACK_OPTION:
                return await self.async_step_sensors()

            # Handle multi-station case
            if multi_station and hasattr(self.flow_context, 'stations'):
                return self.async_create_entry(
                    title=build_entry_title(
                        self.flow_context.stations,
                        multi_station=True,
                    ),
                    data=build_entry_data(
                        self.flow_context.stations,
                        self.flow_context.enabled_sensors,
                        multi_station=True,
                    ),
                )
            else:
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


class OsmerFvgOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle OSMER FVG options flow."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current options
        current_options = self.config_entry.options
        current_enabled = current_options.get(
            "enabled_sensors",
            self.config_entry.data.get("enabled_sensors", []),
        )
        current_scan_interval = current_options.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL.total_seconds() / 60,
        )
        current_retry_count = current_options.get(
            CONF_RETRY_COUNT,
            DEFAULT_RETRY_COUNT,
        )
        current_retry_delay = current_options.get(
            CONF_RETRY_DELAY,
            DEFAULT_RETRY_DELAY,
        )
        current_timeout = current_options.get(
            CONF_TIMEOUT,
            DEFAULT_TIMEOUT,
        )
        current_offline_threshold = current_options.get(
            CONF_OFFLINE_THRESHOLD,
            int(DEFAULT_OFFLINE_THRESHOLD.total_seconds() / 60),
        )

        from .const import CONF_ENABLE_ALERT_NOTIFICATIONS
        
        sensor_options = {
            code: f"{config['name']} ({code})"
            for code, config in MONITORED_SENSORS.items()
        }
        
        # Check if multi-station is enabled
        is_multi_station = self.config_entry.options.get(CONF_MULTI_STATION, False)
        current_station_ids = self.config_entry.options.get(CONF_STATION_IDS, [])
        current_alert_notifications = self.config_entry.options.get(
            CONF_ENABLE_ALERT_NOTIFICATIONS, True
        )

        schema = vol.Schema(
            {
                vol.Required(
                    "enabled_sensors",
                    default=current_enabled,
                ): cv.multi_select(sensor_options),
                vol.Optional(
                    CONF_MULTI_STATION,
                    default=is_multi_station,
                ): bool,
                vol.Optional(
                    CONF_STATION_IDS,
                    default=current_station_ids,
                ): cv.multi_select(
                    {
                        str(s.id): f"{s.name} (ID: {s.id})"
                        for s in self.flow_context.stations
                    }
                ) if is_multi_station and self.flow_context.stations else [],
                vol.Optional(
                    CONF_ENABLE_ALERT_NOTIFICATIONS,
                    default=current_alert_notifications,
                ): bool,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_scan_interval,
                ): vol.All(int, vol.Clamp(min=5, max=120)),
                vol.Optional(
                    CONF_RETRY_COUNT,
                    default=current_retry_count,
                ): vol.All(int, vol.Clamp(min=1, max=5)),
                vol.Optional(
                    CONF_RETRY_DELAY,
                    default=current_retry_delay,
                ): vol.All(int, vol.Clamp(min=1, max=30)),
                vol.Optional(
                    CONF_TIMEOUT,
                    default=current_timeout,
                ): vol.All(int, vol.Clamp(min=10, max=120)),
                vol.Optional(
                    CONF_OFFLINE_THRESHOLD,
                    default=current_offline_threshold,
                ): vol.All(int, vol.Clamp(min=5, max=120)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
