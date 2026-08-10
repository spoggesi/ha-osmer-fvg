"""Coordinator for OSMER FVG integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.client import OsmerApiClient
from .api.models import Measure, OsmerForecastDay, Sensor, Station
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .forecast_zone import get_osmer_zone

_LOGGER = logging.getLogger(__name__)


@dataclass
class OsmerData:
    """Data stored in coordinator."""

    station: Station
    sensors: dict[str, Sensor]
    measures: dict[str, Measure]
    forecasts: list[OsmerForecastDay] = field(default_factory=list)


class OsmerDataUpdateCoordinator(DataUpdateCoordinator[OsmerData]):
    """Data update coordinator for OSMER FVG."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: OsmerApiClient,
        station_id: int,
        enabled_sensors: list[str],
    ) -> None:
        """Initialize coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

        self.client = client
        self.station_id = station_id
        self.enabled_sensors = enabled_sensors

    async def _async_update_data(self) -> OsmerData:
        """Fetch data from OSMER FVG API."""

        try:
            station = await self.client.get_station(self.station_id)
            sensors = await self.client.get_sensors(self.station_id)

            sensors_dict = {
                sensor.code: sensor
                for sensor in sensors
                if sensor.code in self.enabled_sensors
            }

            measures_list = await asyncio.gather(
                *[
                    self.client.get_latest_measure(
                        self.station_id,
                        sensor,
                    )
                    for sensor in sensors_dict.values()
                ],
                return_exceptions=True,
            )

            measures_dict: dict[str, Measure] = {}

            for sensor_code, measure in zip(
                sensors_dict.keys(),
                measures_list,
            ):
                if isinstance(measure, Measure):
                    measures_dict[sensor_code] = measure

            zone = get_osmer_zone(
                station.latitude,
                station.longitude,
                station.altitude,
            )

            forecasts = await self.client.get_forecasts(zone)

            return OsmerData(
                station=station,
                sensors=sensors_dict,
                measures=measures_dict,
                forecasts=forecasts,
            )

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
