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
from ..helpers.distance import distance_km
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
                            label="📡 Seleziona stazione",
                        ),
                        SelectOptionDict(
                            value="address",
                            label="📍 Cerca tramite indirizzo",
                        ),
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
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
                TextSelectorConfig()
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
    latitude: float,
    longitude: float,
) -> vol.Schema:
    """Build nearest station selector."""

    options: list[SelectOptionDict] = []

    for station in stations:

        distance = distance_km(
            latitude,
            longitude,
            station.latitude,
            station.longitude,
        )

        label = station_label(
            station,
            station_sensors.get(
                station.id,
                [],
            ),
        )

        options.append(
            SelectOptionDict(
                value=str(station.id),
                label=f"{label} - {distance:.1f} km",
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
                default=[
                    sensor.code
                    for sensor in sensors
                ],
            ): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            )
        }
    )