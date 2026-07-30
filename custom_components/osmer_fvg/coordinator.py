"""Data coordinator for the OSMER FVG integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.client import OsmerApiClient
from .api.exceptions import (
    OsmerApiResponseError,
    OsmerConnectionError,
)
from .api.models import Measure, Sensor, Station
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class OsmerData:
    """Container for OSMER station data."""

    station: Station
    sensors: dict[str, Sensor]
    measures: dict[str, Measure]


class OsmerDataUpdateCoordinator(
    DataUpdateCoordinator[OsmerData]
):
    """Coordinator for one OSMER station."""


    def __init__(
        self,
        hass: HomeAssistant,
        client: OsmerApiClient,
        station_id: int,
    ) -> None:
        """Initialize coordinator."""

        self.client = client
        self.station_id = station_id

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=DEFAULT_SCAN_INTERVAL
            ),
        )


    async def _async_update_data(
        self,
    ) -> OsmerData:
        """Fetch station data."""

        try:

            station = await self.client.get_station(
                self.station_id
            )


            sensors_list = await self.client.get_sensors(
                self.station_id
            )


            sensors = {
                sensor.code: sensor
                for sensor in sensors_list
            }


            measures: dict[str, Measure] = {}


            now = datetime.now(
                timezone.utc
            )

            start = now - timedelta(
                hours=1
            )


            for sensor in sensors_list:

                try:

                    data = await self.client.get_measures(
                        station_id=self.station_id,
                        sensor_id=sensor.id,
                        start=start.isoformat(),
                        end=now.isoformat(),
                    )


                    if data:
                        measures[sensor.code] = data[-1]


                except (
                    OsmerApiResponseError,
                    OsmerConnectionError,
                    aiohttp.ClientError,
                ) as err:

                    _LOGGER.warning(
                        "Unable to fetch %s: %s",
                        sensor.code,
                        err,
                    )


            return OsmerData(
                station=station,
                sensors=sensors,
                measures=measures,
            )


        except (
            OsmerApiResponseError,
            OsmerConnectionError,
            aiohttp.ClientError,
        ) as err:

            raise UpdateFailed(
                f"Unable to fetch OSMER data: {err}"
            ) from err