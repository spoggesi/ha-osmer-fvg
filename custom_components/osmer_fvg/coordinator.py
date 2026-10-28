"""Coordinator for OSMER FVG integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.client import OsmerApiClient
from .api.models import Measure, OsmerForecastDay, Sensor, Station
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, VERSION
from .forecast_zone import get_osmer_zone

_LOGGER = logging.getLogger(__name__)

# Cache configuration
COORDINATOR_CACHE_VERSION = 1
COORDINATOR_CACHE_KEY = "osmer_fvg_coordinator_cache"
COORDINATOR_CACHE_TTL_DAYS = 30


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

        # Persistent cache
        self._cache_store = Store(
            hass,
            COORDINATOR_CACHE_VERSION,
            f"{COORDINATOR_CACHE_KEY}_{station_id}",
        )
        self._cache_data: dict[str, Any] = {}
        self._cache_loaded: bool = False

        # Cache in memoria per i metadati della stazione e dei sensori
        self._station: Station | None = None
        self._sensors_dict: dict[str, Sensor] | None = None
        self._zone: str | None = None

    async def _async_load_cache(self) -> None:
        """Load coordinator cache from disk."""
        if self._cache_loaded:
            return
        stored = await self._cache_store.async_load()
        if stored:
            self._cache_data = stored
            self._cache_loaded = True
            _LOGGER.debug("Loaded coordinator cache for station %s", self.station_id)

    async def _async_save_cache(self) -> None:
        """Save coordinator cache to disk."""
        self._cache_data["version"] = COORDINATOR_CACHE_VERSION
        self._cache_data["updated"] = datetime.now(UTC).isoformat()
        self._cache_data["version_integration"] = VERSION
        await self._cache_store.async_save(self._cache_data)
        _LOGGER.debug("Saved coordinator cache for station %s", self.station_id)

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache_loaded or not self._cache_data:
            return False
        if self._cache_data.get("version") != COORDINATOR_CACHE_VERSION:
            return False
        timestamp = self._cache_data.get("updated")
        if not timestamp:
            return False
        try:
            updated = datetime.fromisoformat(timestamp)
            return datetime.now(UTC) - updated <= timedelta(days=COORDINATOR_CACHE_TTL_DAYS)
        except ValueError:
            return False

    def _get_cached_station(self) -> Station | None:
        """Get station from cache if available."""
        station_data = self._cache_data.get("station")
        if station_data:
            try:
                return Station(**station_data)
            except (TypeError, KeyError):
                return None
        return None

    def _get_cached_sensors(self) -> dict[str, Sensor]:
        """Get sensors from cache if available."""
        sensors_data = self._cache_data.get("sensors", {})
        result: dict[str, Sensor] = {}
        for code, sensor_data in sensors_data.items():
            if code in self.enabled_sensors:
                try:
                    result[code] = Sensor(**sensor_data)
                except (TypeError, KeyError):
                    continue
        return result

    async def _async_update_data(self) -> OsmerData:
        """Fetch data from OSMER FVG API."""

        try:
            # Load cache on first call
            if not self._cache_loaded:
                await self._async_load_cache()

            # 1. Recupera i dati della stazione (da cache o API)
            if self._station is None:
                # Prova a caricare da cache
                self._station = self._get_cached_station()
                if self._station is None:
                    # Carica da API
                    self._station = await self.client.get_station(self.station_id)
                    # Salva in cache
                    self._cache_data["station"] = self._station.__dict__
                    await self._async_save_cache()

            # 2. Recupera l'elenco dei sensori (da cache o API)
            if self._sensors_dict is None:
                self._sensors_dict = self._get_cached_sensors()
                if not self._sensors_dict:
                    # Carica da API
                    sensors = await self.client.get_sensors(self.station_id)
                    self._sensors_dict = {
                        sensor.code: sensor
                        for sensor in sensors
                        if sensor.code in self.enabled_sensors
                    }
                    # Salva in cache
                    self._cache_data["sensors"] = {
                        code: sensor.__dict__
                        for code, sensor in self._sensors_dict.items()
                    }
                    await self._async_save_cache()

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
