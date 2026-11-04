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
from .api.models import Measure, OsmerAlert, OsmerForecastDay, Sensor, Station
from .const import (
    CONF_OFFLINE_THRESHOLD,
    CONF_RETRY_COUNT,
    CONF_RETRY_DELAY,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_OFFLINE_THRESHOLD,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    VERSION,
)
from .forecast_zone import get_osmer_zone

_LOGGER = logging.getLogger(__name__)

# Cache configuration
COORDINATOR_CACHE_VERSION = 2
COORDINATOR_CACHE_KEY = "osmer_fvg_coordinator_cache"
COORDINATOR_CACHE_TTL_DAYS = 30  # For station and sensor metadata
COORDINATOR_MEASURES_CACHE_TTL_MINUTES = 15  # For measurements data
COORDINATOR_FORECAST_CACHE_TTL_MINUTES = 30  # For forecast data
COORDINATOR_ALERTS_CACHE_TTL_MINUTES = 15  # For alerts data


@dataclass
class OsmerData:
    """Data stored in coordinator."""

    station: Station
    sensors: dict[str, Sensor]
    measures: dict[str, Measure]
    forecasts: list[OsmerForecastDay] = field(default_factory=list)
    alerts: list[OsmerAlert] = field(default_factory=list)


class OsmerDataUpdateCoordinator(DataUpdateCoordinator[OsmerData]):
    """Data update coordinator for OSMER FVG."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: OsmerApiClient,
        station_id: int,
        enabled_sensors: list[str],
        options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize coordinator."""

        # Calculate scan interval from options
        scan_interval_minutes = DEFAULT_SCAN_INTERVAL.total_seconds() / 60
        if options and CONF_SCAN_INTERVAL in options:
            scan_interval_minutes = options[CONF_SCAN_INTERVAL]
        scan_interval = timedelta(minutes=scan_interval_minutes)

        # Store options for use in update method
        self._options = options or {}
        self._retry_count = self._options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT)
        self._retry_delay = self._options.get(CONF_RETRY_DELAY, DEFAULT_RETRY_DELAY)
        self._timeout = self._options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        self._offline_threshold = timedelta(
            minutes=self._options.get(
                CONF_OFFLINE_THRESHOLD,
                int(DEFAULT_OFFLINE_THRESHOLD.total_seconds() / 60),
            )
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
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
        
        # Last known data for offline support
        self._last_known_data: OsmerData | None = None
        self._osmer_last_update_success: datetime | None = None

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

    def _is_cache_valid(self, cache_type: str = "metadata") -> bool:
        """Check if cache is still valid for a specific type.
        
        Args:
            cache_type: Type of cache to validate
                - "metadata": Station and sensor data (30 days TTL)
                - "measures": Measurement data (15 minutes TTL)
                - "forecast": Forecast data (30 minutes TTL)
                - "alerts": Alert data (15 minutes TTL)
        """
        if not self._cache_loaded or not self._cache_data:
            return False
        if self._cache_data.get("version") != COORDINATOR_CACHE_VERSION:
            return False
        
        timestamp = self._cache_data.get("updated")
        if not timestamp:
            return False
        
        try:
            updated = datetime.fromisoformat(timestamp)
            now = datetime.now(UTC)
            
            if cache_type == "metadata":
                ttl = timedelta(days=COORDINATOR_CACHE_TTL_DAYS)
            elif cache_type == "measures":
                ttl = timedelta(minutes=COORDINATOR_MEASURES_CACHE_TTL_MINUTES)
            elif cache_type == "forecast":
                ttl = timedelta(minutes=COORDINATOR_FORECAST_CACHE_TTL_MINUTES)
            elif cache_type == "alerts":
                ttl = timedelta(minutes=COORDINATOR_ALERTS_CACHE_TTL_MINUTES)
            else:
                ttl = timedelta(days=COORDINATOR_CACHE_TTL_DAYS)
            
            return (now - updated) <= ttl
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
        """Fetch data from OSMER FVG API with retry logic."""

        _LOGGER.debug(
            "Starting data update for station %s, sensors: %s",
            self.station_id,
            list(self.enabled_sensors),
        )

        try:
            # Load cache on first call
            if not self._cache_loaded:
                await self._async_load_cache()
                _LOGGER.debug("Cache loaded for station %s", self.station_id)

            # 1. Recupera i dati della stazione (da cache o API con retry)
            # Usiamo TTL lungo per i metadati della stazione
            if self._station is None:
                if self._is_cache_valid("metadata"):
                    self._station = self._get_cached_station()
                if self._station is None:
                    self._station = await self._fetch_with_retry(
                        self.client.get_station,
                        self.station_id,
                        operation_name="station data",
                    )
                    if self._station:
                        self._cache_data["station"] = self._station.__dict__
                        await self._async_save_cache()
                        _LOGGER.debug("Fetched station %s from API", self.station_id)

            # 2. Recupera l'elenco dei sensori (da cache o API con retry)
            # Usiamo TTL lungo per i metadati dei sensori
            if self._sensors_dict is None:
                if self._is_cache_valid("metadata"):
                    self._sensors_dict = self._get_cached_sensors()
                if not self._sensors_dict:
                    sensors = await self._fetch_with_retry(
                        self.client.get_sensors,
                        self.station_id,
                        operation_name="sensors list",
                    )
                    if sensors:
                        self._sensors_dict = {
                            sensor.code: sensor
                            for sensor in sensors
                            if sensor.code in self.enabled_sensors
                        }
                        self._cache_data["sensors"] = {
                            code: sensor.__dict__
                            for code, sensor in self._sensors_dict.items()
                        }
                        await self._async_save_cache()
                        _LOGGER.debug("Fetched %d sensors for station %s",
                                    len(sensors), self.station_id)

            # 3. Scarica le misurazioni con retry per ogni sensore
            measures_dict: dict[str, Measure] = {}
            
            for sensor_code, sensor in self._sensors_dict.items():
                for attempt in range(self._retry_count):
                    try:
                        measure = await asyncio.wait_for(
                            self.client.get_latest_measure(self.station_id, sensor),
                            timeout=self._timeout,
                        )
                        if measure:
                            measures_dict[sensor_code] = measure
                            _LOGGER.debug(
                                "Fetched measure for sensor %s: %s = %s",
                                sensor_code,
                                sensor.name,
                                measure.value,
                            )
                        break
                    except (TimeoutError, asyncio.CancelledError) as err:
                        _LOGGER.warning(
                            "Attempt %d/%d timeout for sensor %s: %s",
                            attempt + 1,
                            self._retry_count,
                            sensor_code,
                            err,
                        )
                        if attempt < self._retry_count - 1:
                            await asyncio.sleep(self._retry_delay)
                    except Exception:  # noqa: BLE001
                        _LOGGER.warning(
                            "Attempt %d/%d failed for sensor %s",
                            attempt + 1,
                            self._retry_count,
                            sensor_code,
                        )
                        if attempt < self._retry_count - 1:
                            await asyncio.sleep(self._retry_delay)

            # 4. Determina la zona meteo solo la prima volta
            if self._zone is None:
                self._zone = get_osmer_zone(
                    self._station.latitude,
                    self._station.longitude,
                    self._station.altitude,
                )
                _LOGGER.debug("Determined forecast zone: %s", self._zone)

            # 5. Scarica le previsioni meteo con retry
            forecasts = []
            for attempt in range(self._retry_count):
                try:
                    forecasts = await asyncio.wait_for(
                        self.client.get_forecasts(self._zone),
                        timeout=self._timeout,
                    )
                    if forecasts:
                        _LOGGER.debug("Fetched %d forecast days", len(forecasts))
                        break
                except (TimeoutError, asyncio.CancelledError):
                    _LOGGER.warning(
                        "Attempt %d/%d timeout for forecasts",
                        attempt + 1,
                        self._retry_count,
                    )
                    if attempt < self._retry_count - 1:
                        await asyncio.sleep(self._retry_delay)
                except Exception:  # noqa: BLE001
                    _LOGGER.warning(
                        "Attempt %d/%d failed for forecasts",
                        attempt + 1,
                        self._retry_count,
                    )
                    if attempt < self._retry_count - 1:
                        await asyncio.sleep(self._retry_delay)

            # 6. Scarica le allerte con retry
            alerts = []
            for attempt in range(self._retry_count):
                try:
                    alerts = await asyncio.wait_for(
                        self.client.get_alerts(),
                        timeout=self._timeout,
                    )
                    if alerts:
                        _LOGGER.debug("Fetched %d alerts", len(alerts))
                    break
                except (TimeoutError, asyncio.CancelledError):
                    _LOGGER.warning(
                        "Attempt %d/%d timeout for alerts",
                        attempt + 1,
                        self._retry_count,
                    )
                    if attempt < self._retry_count - 1:
                        await asyncio.sleep(self._retry_delay)
                except Exception:  # noqa: BLE001
                    _LOGGER.warning(
                        "Attempt %d/%d failed for alerts",
                        attempt + 1,
                        self._retry_count,
                    )
                    if attempt < self._retry_count - 1:
                        await asyncio.sleep(self._retry_delay)

            # Log completion
            _LOGGER.debug(
                "Data update completed for station %s: %d sensors, %d forecasts, %d alerts",
                self.station_id,
                len(measures_dict),
                len(forecasts),
                len(alerts),
            )

            # Store last known successful data
            result = OsmerData(
                station=self._station,
                sensors=self._sensors_dict,
                measures=measures_dict,
                forecasts=forecasts,
                alerts=alerts,
            )
            self._last_known_data = result
            self._osmer_last_update_success = datetime.now(UTC)

            return result

        except Exception:
            _LOGGER.exception(
                "Error updating data for station %s",
                self.station_id,
            )
            
            # Check if we have stale data (beyond offline threshold)
            now = datetime.now(UTC)
            if (
                self._last_known_data is not None
                and self._osmer_last_update_success is not None
                and (now - self._osmer_last_update_success) > self._offline_threshold
            ):
                _LOGGER.warning(
                    "Using stale data for station %s (last update: %s)",
                    self.station_id,
                    self._osmer_last_update_success.isoformat(),
                )
                # Return last known data even if stale
                return self._last_known_data
            
            # If we have no data at all, raise the error
            if self._last_known_data is None:
                raise UpdateFailed("Error communicating with API")
            
            # Return last known data
            return self._last_known_data

    async def _fetch_with_retry(
        self,
        func: Any,
        *args: Any,
        operation_name: str,
    ) -> Any:
        """Execute function with retry logic."""
        last_error = None
        for attempt in range(self._retry_count):
            try:
                result = await asyncio.wait_for(
                    func(*args),
                    timeout=self._timeout,
                )
                return result
            except (TimeoutError, asyncio.CancelledError) as err:
                last_error = err
                _LOGGER.warning(
                    "Attempt %d/%d timeout for %s",
                    attempt + 1,
                    self._retry_count,
                    operation_name,
                )
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay)
            except Exception as err:  # noqa: BLE001
                last_error = err
                _LOGGER.warning(
                    "Attempt %d/%d failed for %s",
                    attempt + 1,
                    self._retry_count,
                    operation_name,
                )
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay)
        
        _LOGGER.error(
            "All %d attempts failed for %s",
            self._retry_count,
            operation_name,
        )
        raise last_error

    @property
    def is_offline(self) -> bool:
        """Check if coordinator is in offline mode (using stale data)."""
        if self._osmer_last_update_success is None:
            return False
        now = datetime.now(UTC)
        return (now - self._osmer_last_update_success) > self._offline_threshold

    @property
    def osmer_last_update_success(self) -> datetime | None:
        """Return timestamp of last successful update."""
        return self._osmer_last_update_success
