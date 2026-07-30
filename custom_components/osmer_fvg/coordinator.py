"""Data coordinator for OSMER FVG."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

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
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MONITORED_SENSORS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class OsmerData:
    """Coordinator data."""

    station: Station
    sensors: dict[str, Sensor]
    measures: dict[str, Measure]


class OsmerDataUpdateCoordinator(
    DataUpdateCoordinator[OsmerData],
):
    """Coordinator for OSMER weather data."""


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
                seconds=DEFAULT_SCAN_INTERVAL,
            ),
        )


    async def _async_update_data(
        self,
    ) -> OsmerData:
        """Fetch data from OSMER API."""

        try:

            station = await self.client.get_station(
                self.station_id,
            )


            sensors_data = await self.client.get_sensors(
                self.station_id,
            )


            sensors: dict[str, Sensor] = {}
            measures: dict[str, Measure] = {}


            now = datetime.now(
                timezone.utc,
            )

            start = now - timedelta(
                hours=3,
            )


            for sensor in sensors_data:

                if sensor.code not in MONITORED_SENSORS:
                    continue


                sensors[sensor.code] = sensor


                try:

                    values = await self.client.get_measures(
                        station_id=self.station_id,
                        sensor_id=sensor.id,
                        start=start.isoformat(),
                        end=now.isoformat(),
                    )


                except (
                    OsmerConnectionError,
                    OsmerApiResponseError,
                ) as err:

                    _LOGGER.warning(
                        "Unable to fetch %s: %s",
                        sensor.code,
                        err,
                    )

                    continue


                if values:

                    measures[sensor.code] = values[-1]


            return OsmerData(
                station=station,
                sensors=sensors,
                measures=measures,
            )


        except (
            OsmerConnectionError,
            OsmerApiResponseError,
        ) as err:

            raise UpdateFailed(
                f"Unable to fetch OSMER data: {err}",
            ) from err