"""Client for the OSMER FVG API."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

from ..logging import api_logger, set_request_id
from .exceptions import (
    OsmerApiError,
    OsmerApiResponseError,
    OsmerConnectionError,
)
from .models import Measure, OsmerAlert, OsmerForecastDay, Sensor, Station
from .parser import (
    parse_measure,
    parse_sensor,
    parse_station,
)
from .xml_parser import parse_osmer_forecast_xml

# Keep standard logger for compatibility
_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://monitor.protezionecivile.fvg.it/api"


class OsmerApiClient:
    """Client for the OSMER API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        timeout: int = 30,
    ) -> None:
        """Initialize client."""

        self._session = session
        self._timeout = timeout
        self._xml_cache: str | None = None
        self._xml_cache_time: datetime | None = None

    async def _get(
        self,
        endpoint: str,
    ) -> dict[str, Any]:
        """Execute GET request."""
        request_id = set_request_id()
        url = f"{BASE_URL}{endpoint}"

        api_logger.debug(
            "API GET request",
            url=url,
            timeout=self._timeout,
            request_id=request_id,
        )

        try:
            async with self._session.get(
                url,
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()
                api_logger.debug(
                    "API response received",
                    url=url,
                    status=response.status,
                    response_size_bytes=len(str(data)),
                    request_id=request_id,
                )
                return data

        except aiohttp.ClientError as err:
            api_logger.error(
                "API connection error",
                url=url,
                error=str(err),
                request_id=request_id,
            )
            raise OsmerConnectionError(f"Unable to connect to {url}") from err

    async def get_stations(self) -> list[Station]:
        """Return available stations."""

        data = await self._get("/stations")

        if data.get("result") != "OK":
            raise OsmerApiResponseError("Unexpected stations response")

        stations = data.get("stations")

        if stations is None:
            raise OsmerApiResponseError("Missing stations")

        return [parse_station(station) for station in stations]

    async def get_station(
        self,
        station_id: int,
    ) -> Station:
        """Return a single station."""

        stations = await self.get_stations()

        for station in stations:
            if station.id == station_id:
                return station

        raise OsmerApiResponseError(f"Station {station_id} not found")

    async def get_sensors(
        self,
        station_id: int,
    ) -> list[Sensor]:
        """Return sensors for station."""

        data = await self._get(f"/stations/{station_id}/sensors")

        if data.get("result") != "OK":
            raise OsmerApiResponseError("Unexpected sensors response")

        sensors = data.get("sensors")

        if sensors is None:
            raise OsmerApiResponseError("Missing sensors")

        return [parse_sensor(sensor) for sensor in sensors]

    async def get_sensor_by_code(
        self,
        station_id: int,
        code: str,
    ) -> Sensor | None:
        """Return sensor by code."""

        sensors = await self.get_sensors(station_id)

        for sensor in sensors:
            if sensor.code == code:
                return sensor

        return None

    async def get_measures(
        self,
        station_id: int,
        sensor_id: int,
        start: str,
        end: str,
    ) -> list[Measure]:
        """Return sensor measurements."""

        data = await self._get(
            f"/stations/{station_id}/sensors/{sensor_id}/measures?from={start}&to={end}"
        )

        if data.get("result") != "OK":
            raise OsmerApiResponseError("Unexpected measures response")

        measures = data.get("measures")

        if measures is None:
            raise OsmerApiResponseError("Missing measures")

        return [parse_measure(measure) for measure in measures]

    async def get_latest_measure(
        self,
        station_id: int,
        sensor: Sensor,
    ) -> Measure | None:
        """Return latest sensor value."""

        now = datetime.now(UTC)

        start = now - timedelta(hours=3)

        measures = await self.get_measures(
            station_id=station_id,
            sensor_id=sensor.id,
            start=start.isoformat(),
            end=now.isoformat(),
        )

        if not measures:
            return None

        return measures[-1]

    async def get_forecasts(
        self,
        zone: str,
    ) -> list[OsmerForecastDay]:
        """Return forecast for zone directly from OSMER XML bulletin with 15-min RAM cache."""
        request_id = set_request_id()
        now = datetime.now(UTC)

        if (
            self._xml_cache
            and self._xml_cache_time
            and (now - self._xml_cache_time) < timedelta(minutes=15)
        ):
            api_logger.debug(
                "Using cached forecast XML",
                zone=zone,
                cache_age_minutes=(now - self._xml_cache_time).total_seconds() / 60,
                request_id=request_id,
            )
            forecasts = parse_osmer_forecast_xml(self._xml_cache, zone)
            if forecasts:
                return forecasts

        dates_to_try = [
            now.strftime("%Y%m%d"),
            (now - timedelta(days=1)).strftime("%Y%m%d"),
            (now - timedelta(days=2)).strftime("%Y%m%d"),
        ]

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        }

        for date_str in dates_to_try:
            url = f"https://dev.meteo.fvg.it/xml/previsioni/PW{date_str}.xml"
            api_logger.debug(
                "Fetching forecast XML",
                url=url,
                date=date_str,
                request_id=request_id,
            )
            try:
                async with self._session.get(
                    url, headers=headers, timeout=5
                ) as response:
                    api_logger.debug(
                        "HTTP response",
                        url=url,
                        status=response.status,
                        request_id=request_id,
                    )
                    if response.status == 200:
                        xml_text = await response.text()
                        if not xml_text.strip().startswith(("<!DOCTYPE", "<html")):
                            self._xml_cache = xml_text
                            self._xml_cache_time = now

                            forecasts = parse_osmer_forecast_xml(xml_text, zone)
                            api_logger.info(
                                "Parsed forecast XML",
                                zone=zone,
                                forecast_count=len(forecasts),
                                url=url,
                                request_id=request_id,
                            )
                            if forecasts:
                                return forecasts
            except (
                aiohttp.ClientError,
                OsmerApiError,
                UnicodeDecodeError,
            ) as err:
                api_logger.debug(
                    "Error fetching XML forecast",
                    url=url,
                    error=str(err),
                    request_id=request_id,
                )

        api_logger.warning(
            "Could not retrieve forecast days",
            zone=zone,
            dates_tried=dates_to_try,
            request_id=request_id,
        )
        return []

    async def get_alerts(self) -> list[OsmerAlert]:
        """Return active alerts from OSMER FVG API.
        
        Note: Alerts endpoint may not be available in all OSMER API versions.
        Returns empty list if endpoint doesn't exist or returns error.
        """
        request_id = set_request_id()
        url = f"{BASE_URL}/alerts"
        api_logger.debug(
            "Fetching alerts",
            url=url,
            request_id=request_id,
        )
        
        try:
            data = await self._get("/alerts")
            
            if data.get("result") != "OK":
                api_logger.debug(
                    "Unexpected alerts response",
                    response_result=data.get("result"),
                    request_id=request_id,
                )
                return []
            
            alerts_data = data.get("alerts", [])
            if not alerts_data:
                api_logger.debug(
                    "No active alerts found",
                    request_id=request_id,
                )
                return []
            
            alerts = []
            for alert_data in alerts_data:
                try:
                    alert = OsmerAlert(
                        id=str(alert_data.get("id", "")),
                        title=str(alert_data.get("title", "")),
                        description=str(alert_data.get("description", "")),
                        level=str(alert_data.get("level", "green")),
                        type=str(alert_data.get("type", "unknown")),
                        start_time=self._parse_datetime(alert_data.get("start_time")),
                        end_time=self._parse_datetime(alert_data.get("end_time")),
                        zones=alert_data.get("zones", []),
                    )
                    alerts.append(alert)
                    api_logger.debug(
                        "Parsed alert",
                        alert_id=alert.id,
                        alert_title=alert.title,
                        alert_level=alert.level,
                        request_id=request_id,
                    )
                except (KeyError, TypeError, ValueError) as err:
                    api_logger.warning(
                        "Error parsing alert",
                        error=str(err),
                        alert_data=str(alert_data)[:100],
                        request_id=request_id,
                    )
                    continue
            
            api_logger.info(
                "Fetched alerts",
                alert_count=len(alerts),
                request_id=request_id,
            )
            return alerts
            
        except Exception:  # noqa: BLE001 - We want to catch all exceptions and return empty list
            api_logger.debug(
                "Alerts endpoint not available",
                error="404 or other error",
                request_id=request_id,
            )
            return []

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        """Parse datetime from various formats."""
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                # Try ISO format first
                return datetime.fromisoformat(value)
            return None
        except (ValueError, TypeError):
            return None
