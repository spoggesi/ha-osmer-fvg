"""Data coordinator for OSMER FVG."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

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
from .api.models import (
    Measure,
    Sensor,
    Station,
)
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
        enabled_sensors: list[str] | None = None,
    ) -> None:
        """Initialize coordinator."""

        self.client = client
        self.station_id = station_id
        self.enabled_sensors = enabled_sensors or []

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=DEFAULT_SCAN_INTERVAL,
            ),
        )

    async def _async_fetch_measure(
        self,
        sensor: Sensor,
        start_iso: str,
        end_iso: str,
    ) -> tuple[str, Measure | None]:
        """Fetch measures for a single sensor asynchronously."""
        try:
            values = await self.client.get_measures(
                station_id=self.station_id,
                sensor_id=sensor.id,
                start=start_iso,
                end=end_iso,
            )
            if values:
                return sensor.code, values[-1]
        except (
            OsmerConnectionError,
            OsmerApiResponseError,
        ) as err:
            _LOGGER.warning(
                "Unable to fetch %s: %s",
                sensor.code,
                err,
            )

        return sensor.code, None

    async def _async_update_data(
        self,
    ) -> OsmerData:
        """Fetch data from OSMER API."""

        try:
            # Recupera dati stazione e lista sensori disponibili
            station = await self.client.get_station(
                self.station_id,
            )

            sensors_data = await self.client.get_sensors(
                self.station_id,
            )

            sensors: dict[str, Sensor] = {}
            target_sensors: list[Sensor] = []

            for sensor in sensors_data:
                if (
                    sensor.code in MONITORED_SENSORS
                    and sensor.code in self.enabled_sensors
                ):
                    sensors[sensor.code] = sensor
                    target_sensors.append(sensor)

            now = datetime.now(UTC)
            start = now - timedelta(hours=3)
            start_iso = start.isoformat()
            end_iso = now.isoformat()

            # Esegue tutte le chiamate API per le misurazioni in parallelo
            tasks = [
                self._async_fetch_measure(sensor, start_iso, end_iso)
                for sensor in target_sensors
            ]

            results = await asyncio.gather(*tasks)

            measures: dict[str, Measure] = {}
            for code, measure in results:
                if measure is not None:
                    measures[code] = measure

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
