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
    CONF_ENABLE_ALERT_NOTIFICATIONS,
    CONF_OFFLINE_THRESHOLD,
    CONF_RETRY_COUNT,
    CONF_RETRY_DELAY,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_ENABLE_ALERT_NOTIFICATIONS,
    DEFAULT_OFFLINE_THRESHOLD,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    VERSION,
)
from .forecast_zone import get_osmer_zone
from .logging import coordinator_logger, reset_request_id, set_request_id

# Keep standard logger for compatibility
_LOGGER = logging.getLogger(__name__)

# Cache configuration
COORDINATOR_CACHE_VERSION = 1
COORDINATOR_CACHE_KEY = "osmer_fvg_coordinator_cache_v2"
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
        
        # Alert notification tracking
        self._last_known_alerts: list[OsmerAlert] = []
        self._alert_notifications_enabled: bool = (
            self._options.get(CONF_ENABLE_ALERT_NOTIFICATIONS, DEFAULT_ENABLE_ALERT_NOTIFICATIONS)
        )

    async def _async_load_cache(self) -> None:
        """Load coordinator cache from disk."""
        request_id = set_request_id()
        if self._cache_loaded:
            coordinator_logger.debug(
                "Cache already loaded, skipping",
                station_id=self.station_id,
                request_id=request_id,
            )
            return
        stored = await self._cache_store.async_load()
        if stored:
            self._cache_data = stored
            self._cache_loaded = True
            coordinator_logger.debug(
                "Loaded coordinator cache",
                station_id=self.station_id,
                cache_version=self._cache_data.get("version"),
                request_id=request_id,
            )

    async def _async_save_cache(self) -> None:
        """Save coordinator cache to disk."""
        request_id = set_request_id()
        self._cache_data["version"] = COORDINATOR_CACHE_VERSION
        self._cache_data["updated"] = datetime.now(UTC).isoformat()
        self._cache_data["version_integration"] = VERSION
        await self._cache_store.async_save(self._cache_data)
        coordinator_logger.debug(
            "Saved coordinator cache",
            station_id=self.station_id,
            cache_size_bytes=len(str(self._cache_data)),
            request_id=request_id,
        )

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
        request_id = set_request_id()
        coordinator_logger.info(
            "Starting data update",
            station_id=self.station_id,
            enabled_sensors=list(self.enabled_sensors),
            retry_count=self._retry_count,
            retry_delay=self._retry_delay,
            timeout=self._timeout,
            request_id=request_id,
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
                    coordinator_logger.debug(
                        "Using cached station data",
                        station_id=self.station_id,
                        request_id=request_id,
                    )
                if self._station is None:
                    self._station = await self._fetch_with_retry(
                        self.client.get_station,
                        self.station_id,
                        operation_name="station data",
                    )
                    if self._station:
                        self._cache_data["station"] = self._station.__dict__
                        await self._async_save_cache()
                        coordinator_logger.info(
                            "Fetched station from API",
                            station_id=self.station_id,
                            station_name=self._station.name,
                            request_id=request_id,
                        )

            # 2. Recupera l'elenco dei sensori (da cache o API con retry)
            # Usiamo TTL lungo per i metadati dei sensori
            if self._sensors_dict is None:
                if self._is_cache_valid("metadata"):
                    self._sensors_dict = self._get_cached_sensors()
                    coordinator_logger.debug(
                        "Using cached sensors data",
                        station_id=self.station_id,
                        sensor_count=len(self._sensors_dict),
                        request_id=request_id,
                    )
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
                        coordinator_logger.info(
                            "Fetched sensors from API",
                            station_id=self.station_id,
                            total_sensors=len(sensors),
                            enabled_sensors=len(self._sensors_dict),
                            request_id=request_id,
                        )

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
                            coordinator_logger.debug(
                                "Fetched measure",
                                sensor_code=sensor_code,
                                sensor_name=sensor.name,
                                value=measure.value,
                                unit=sensor.unit,
                                attempt=attempt + 1,
                                request_id=request_id,
                            )
                        break
                    except (TimeoutError, asyncio.CancelledError) as err:
                        coordinator_logger.warning(
                            "Measure fetch timeout",
                            sensor_code=sensor_code,
                            attempt=attempt + 1,
                            retry_count=self._retry_count,
                            error=str(err),
                            request_id=request_id,
                        )
                        if attempt < self._retry_count - 1:
                            await asyncio.sleep(self._retry_delay)
                    except Exception as err:  # noqa: BLE001
                        coordinator_logger.warning(
                            "Measure fetch failed",
                            sensor_code=sensor_code,
                            attempt=attempt + 1,
                            retry_count=self._retry_count,
                            error=str(err),
                            request_id=request_id,
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
                coordinator_logger.debug(
                    "Determined forecast zone",
                    zone=self._zone,
                    latitude=self._station.latitude,
                    longitude=self._station.longitude,
                    altitude=self._station.altitude,
                    request_id=request_id,
                )

            # 5. Scarica le previsioni meteo con retry
            forecasts = []
            for attempt in range(self._retry_count):
                try:
                    forecasts = await asyncio.wait_for(
                        self.client.get_forecasts(self._zone),
                        timeout=self._timeout,
                    )
                    if forecasts:
                        coordinator_logger.info(
                            "Fetched forecasts",
                            zone=self._zone,
                            forecast_count=len(forecasts),
                            request_id=request_id,
                        )
                        break
                except (TimeoutError, asyncio.CancelledError) as err:
                    coordinator_logger.warning(
                        "Forecast fetch timeout",
                        zone=self._zone,
                        attempt=attempt + 1,
                        retry_count=self._retry_count,
                        error=str(err),
                        request_id=request_id,
                    )
                    if attempt < self._retry_count - 1:
                        await asyncio.sleep(self._retry_delay)
                except Exception as err:  # noqa: BLE001
                    coordinator_logger.warning(
                        "Forecast fetch failed",
                        zone=self._zone,
                        attempt=attempt + 1,
                        retry_count=self._retry_count,
                        error=str(err),
                        request_id=request_id,
                    )
                    if attempt < self._retry_count - 1:
                        await asyncio.sleep(self._retry_delay)

            # 6. Scarica le allerte con retry
            # Note: Alerts endpoint may not exist (404), so we catch connection errors
            alerts = []
            try:
                alerts = await asyncio.wait_for(
                    self.client.get_alerts(),
                    timeout=self._timeout,
                )
                if alerts:
                    coordinator_logger.info(
                        "Fetched alerts",
                        alert_count=len(alerts),
                        request_id=request_id,
                    )
            except (TimeoutError, asyncio.CancelledError) as err:
                coordinator_logger.debug(
                    "Alert fetch timed out",
                    error=str(err),
                    request_id=request_id,
                )
            except Exception:  # noqa: BLE001 - Alerts endpoint may not exist
                # Don't log errors for alerts endpoint as it may not be available
                coordinator_logger.debug(
                    "Alerts endpoint not available, continuing without alerts",
                    request_id=request_id,
                )

            # Log completion
            coordinator_logger.info(
                "Data update completed",
                station_id=self.station_id,
                measures_count=len(measures_dict),
                forecasts_count=len(forecasts),
                alerts_count=len(alerts),
                request_id=request_id,
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

            # Check for new alerts and send notifications
            if self._alert_notifications_enabled:
                await self._async_check_alert_notifications(alerts)

            return result

        except Exception as err:  # noqa: BLE001 - We want to catch all exceptions in update
            coordinator_logger.exception(
                "Error updating data",
                station_id=self.station_id,
                error=str(err),
                request_id=request_id,
            )
            reset_request_id()
            
            # Check if we have stale data (beyond offline threshold)
            now = datetime.now(UTC)
            if (
                self._last_known_data is not None
                and self._osmer_last_update_success is not None
                and (now - self._osmer_last_update_success) > self._offline_threshold
            ):
                coordinator_logger.warning(
                    "Using stale data",
                    station_id=self.station_id,
                    last_update=self._osmer_last_update_success.isoformat(),
                    offline_threshold=self._offline_threshold,
                    request_id=request_id,
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
        request_id = set_request_id()
        last_error = None
        for attempt in range(self._retry_count):
            try:
                result = await asyncio.wait_for(
                    func(*args),
                    timeout=self._timeout,
                )
                coordinator_logger.debug(
                    "Fetch with retry succeeded",
                    operation=operation_name,
                    attempt=attempt + 1,
                    request_id=request_id,
                )
                return result
            except (TimeoutError, asyncio.CancelledError) as err:
                last_error = err
                coordinator_logger.warning(
                    "Fetch with retry timeout",
                    operation=operation_name,
                    attempt=attempt + 1,
                    retry_count=self._retry_count,
                    error=str(err),
                    request_id=request_id,
                )
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay)
            except Exception as err:  # noqa: BLE001
                last_error = err
                coordinator_logger.warning(
                    "Fetch with retry failed",
                    operation=operation_name,
                    attempt=attempt + 1,
                    retry_count=self._retry_count,
                    error=str(err),
                    request_id=request_id,
                )
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay)
        
        coordinator_logger.error(
            "All retry attempts failed",
            operation=operation_name,
            retry_count=self._retry_count,
            error=str(last_error) if last_error else "Unknown error",
            request_id=request_id,
        )
        reset_request_id()
        raise last_error

    async def _async_check_alert_notifications(
        self, current_alerts: list[OsmerAlert]
    ) -> None:
        """Check for new or changed alerts and send notifications."""
        request_id = set_request_id()
        
        if not current_alerts:
            # No current alerts, check if we had alerts before
            if self._last_known_alerts:
                coordinator_logger.info(
                    "All alerts cleared",
                    request_id=request_id,
                )
                # Send notification that alerts are cleared
                await self._async_send_alert_notification(
                    "✅ Tutte le allerte sono state revocate",
                    "Non ci sono più allerte meteo attive.",
                    "green",
                    []
                )
            self._last_known_alerts = []
            return
        
        # Compare with last known alerts
        if not self._last_known_alerts:
            # First time we have alerts, notify about all of them
            for alert in current_alerts:
                zones = [alert.zone] if alert.zone else []
                await self._async_send_alert_notification(
                    f"🚨 Nuova allerta: {alert.event_type}",
                    alert.description or "Nessuna descrizione disponibile",
                    alert.level or "unknown",
                    zones
                )
        else:
            # Check for new alerts
            old_alert_ids = {alert.id for alert in self._last_known_alerts}
            new_alert_ids = {alert.id for alert in current_alerts}
            
            # New alerts
            new_alerts = [alert for alert in current_alerts if alert.id not in old_alert_ids]
            for alert in new_alerts:
                zones = [alert.zone] if alert.zone else []
                await self._async_send_alert_notification(
                    f"🚨 Nuova allerta: {alert.event_type}",
                    alert.description or "Nessuna descrizione disponibile",
                    alert.level or "unknown",
                    zones
                )
            
            # Cleared alerts
            cleared_alerts = [alert for alert in self._last_known_alerts if alert.id not in new_alert_ids]
            for alert in cleared_alerts:
                zones = [alert.zone] if alert.zone else []
                await self._async_send_alert_notification(
                    f"✅ Allerta revocata: {alert.event_type}",
                    f"L'allerta per {alert.zone} è stata revocata.",
                    "green",
                    zones
                )
        
        # Update last known alerts
        self._last_known_alerts = current_alerts.copy()

    async def _async_send_alert_notification(
        self, title: str, message: str, level: str, zones: list[str]
    ) -> None:
        """Send an alert notification through Home Assistant."""
        request_id = set_request_id()
        
        # Determine emoji based on level
        level_emoji = {
            "green": "✅",
            "yellow": "⚠️",
            "orange": "🟠",
            "red": "🔴",
        }.get(level.lower(), "🔵")
        
        full_title = f"{level_emoji} OSMER FVG - {title}"
        full_message = f"{message}\n\nLivello: {level.upper()}\nZones: {', '.join(zones) if zones else 'Tutte'}"
        
        coordinator_logger.info(
            "Sending alert notification",
            title=full_title,
            level=level,
            zones=zones,
            request_id=request_id,
        )
        
        try:
            await self.hass.services.async_call(
                "notify",
                "notify",
                {
                    "title": full_title,
                    "message": full_message,
                    "data": {
                        "tag": DOMAIN,
                        "priority": "high" if level.lower() in ["orange", "red"] else "normal",
                        "level": level,
                        "zones": zones,
                    },
                },
            )
        except Exception as err:  # noqa: BLE001 - We want to catch all notification errors
            coordinator_logger.warning(
                "Failed to send alert notification",
                error=str(err),
                request_id=request_id,
            )

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
