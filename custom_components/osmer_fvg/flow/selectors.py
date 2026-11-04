"""Selectors used by the OSMER config flow."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from ..api.models import Sensor, Station
from ..const import CONF_STATION_IDS
from .formatter import (
    sensor_label,
    station_label,
)


def build_selection_method_selector() -> vol.Schema:
    """Build initial selection method selector."""

    return vol.Schema(
        {
            vol.Required(
                "selection_method",
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(
                            value="station",
                            label="📡 Seleziona una stazione",
                        ),
                        SelectOptionDict(
                            value="multi_station",
                            label="📡📡 Seleziona più stazioni",
                        ),
                        SelectOptionDict(
                            value="address",
                            label="📍 Trova stazione vicino a un indirizzo",
                        ),
                    ],
                    mode=SelectSelectorMode.LIST,
                )
            )
        }
    )


def build_address_selector() -> vol.Schema:
    """Build address input selector."""

    return vol.Schema(
        {
            vol.Required(
                "address",
            ): TextSelector(
                TextSelectorConfig(
                    placeholder="Inserisci indirizzo (es: Via Roma, Udine)",
                )
            )
        }
    )


def build_station_selector(
    stations: list[Station],
    station_sensors: dict[int, list[Sensor]],
) -> vol.Schema:
    """Build station selector."""

    options: list[SelectOptionDict] = []

    for station in stations:
        options.append(
            SelectOptionDict(
                value=str(station.id),
                label=station_label(
                    station,
                    station_sensors.get(
                        station.id,
                        [],
                    ),
                ),
            )
        )

    return vol.Schema(
        {
            vol.Required(
                "station",
            ): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def build_nearest_station_selector(
    stations: list[Station],
    station_sensors: dict[int, list[Sensor]],
    latitude: float | None = None,
    longitude: float | None = None,
) -> vol.Schema:
    """Build nearest station selector."""

    options: list[SelectOptionDict] = []

    for station in stations:
        options.append(
            SelectOptionDict(
                value=str(station.id),
                label=station_label(
                    station,
                    station_sensors.get(
                        station.id,
                        [],
                    ),
                    latitude,
                    longitude,
                ),
            )
        )

    return vol.Schema(
        {
            vol.Required(
                "station",
            ): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def build_sensor_selector(
    sensors: list[Sensor],
) -> vol.Schema:
    """Build sensor selector."""

    options: list[SelectOptionDict] = []

    for sensor in sensors:
        options.append(
            SelectOptionDict(
                value=sensor.code,
                label=sensor_label(
                    sensor,
                ),
            )
        )

    return vol.Schema(
        {
            vol.Required(
                "enabled_sensors",
                default=[sensor.code for sensor in sensors],
            ): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            )
        }
    )


def build_back_selector() -> SelectSelector:
    """Build back selector."""

    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(
                    value="__back__",
                    label="⬅️ Indietro",
                )
            ],
            mode=SelectSelectorMode.LIST,
        )
    )


def build_multi_station_selector(
    stations: list[Station],
    station_sensors: dict[int, list[Sensor]],
    selected_stations: list[int] | None = None,
) -> vol.Schema:
    """Build multi-station selector with search/autocomplete."""
    
    options: list[SelectOptionDict] = []
    
    for station in stations:
        options.append(
            SelectOptionDict(
                value=str(station.id),
                label=station_label(
                    station,
                    station_sensors.get(station.id, []),
                ),
            )
        )
    
    return vol.Schema(
        {
            vol.Optional(
                CONF_STATION_IDS,
                default=selected_stations or [],
            ): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                    custom_placeholder="🔍 Cerca e seleziona stazioni...",
                )
            )
        }
    )


def build_station_search_selector(
    stations: list[Station],
    station_sensors: dict[int, list[Sensor]],
) -> vol.Schema:
    """Build station selector with search input for autocomplete."""
    
    # Create options sorted by name for easier searching
    sorted_stations = sorted(stations, key=lambda s: s.name.lower())
    
    options: list[SelectOptionDict] = []
    
    for station in sorted_stations:
        options.append(
            SelectOptionDict(
                value=str(station.id),
                label=station_label(
                    station,
                    station_sensors.get(station.id, []),
                ),
            )
        )
    
    return vol.Schema(
        {
            vol.Required(
                "station_ids",
            ): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                    custom_placeholder="🔍 Inizia a scrivere per cercare una stazione...",
                )
            )
        }
    )
