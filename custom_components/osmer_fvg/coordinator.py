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

        # Cache in memoria per i metadati della stazione e dei sensori
        self._station: Station | None = None
        self._sensors_dict: dict[str, Sensor] | None = None
        self._zone: str | None = None

    async def _async_update_data(self) -> OsmerData:
        """Fetch data from OSMER FVG API."""

        try:
            # 1. Recupera i dati della stazione solo la prima volta
            if self._station is None:
                self._station = await self.client.get_station(self.station_id)

            # 2. Recupera l'elenco dei sensori solo la prima volta
            if self._sensors_dict is None:
                sensors = await self.client.get_sensors(self.station_id)
                self._sensors_dict = {
                    sensor.code: sensor
                    for sensor in sensors
                    if sensor.code in self.enabled_sensors
                }

            # 3. Scarica SOLO le misurazioni per i sensori abilitati
            measures_list = await asyncio.gather(
                *[
                    self.client.get_latest_measure(
                        self.station_id,
                        sensor,
                    )
                    for sensor in self._sensors_dict.values()
                ],
                return_exceptions=True,
            )

            measures_dict: dict[str, Measure] = {}

            for sensor_code, measure in zip(
                self._sensors_dict.keys(),
                measures_list,
            ):
                if isinstance(measure, Measure):
                    measures_dict[sensor_code] = measure

            # 4. Determina la zona meteo solo la prima volta
            if self._zone is None:
                self._zone = get_osmer_zone(
                    self._station.latitude,
                    self._station.longitude,
                    self._station.altitude,
                )

            # 5. Scarica le previsioni meteo
            forecasts = await self.client.get_forecasts(self._zone)

            return OsmerData(
                station=self._station,
                sensors=self._sensors_dict,
                measures=measures_dict,
                forecasts=forecasts,
            )

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
