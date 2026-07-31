"""Selectors used by the OSMER config flow."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from ..api.models import Sensor, Station
from .formatter import (
    sensor_label,
    station_label,
)


def build_station_selector(
    stations: list[Station],
    station_sensors: dict[int, list[Sensor]],
) -> vol.Schema:
    """Build the station selector."""

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


def build_sensor_selector(
    sensors: list[Sensor],
) -> vol.Schema:
    """Build the sensor selector."""

    options: list[SelectOptionDict] = []

    for sensor in sensors:
        options.append(
            SelectOptionDict(
                value=sensor.code,
                label=sensor_label(sensor),
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