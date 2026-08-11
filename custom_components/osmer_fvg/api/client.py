"""Client for the OSMER FVG API."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

from .exceptions import (
    OsmerApiError,
    OsmerApiResponseError,
    OsmerConnectionError,
)
from .models import Measure, OsmerForecastDay, Sensor, Station
from .parser import (
    parse_measure,
    parse_sensor,
    parse_station,
)
from .xml_parser import parse_osmer_forecast_xml

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://monitor.protezionecivile.fvg.it/api"


class OsmerApiClient:
    """Client for the OSMER API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize client."""

        self._session = session
        self._xml_cache: str | None = None
        self._xml_cache_time: datetime | None = None

    async def _get(
        self,
        endpoint: str,
    ) -> dict[str, Any]:
        """Execute GET request."""

        url = f"{BASE_URL}{endpoint}"

        _LOGGER.debug("GET %s", url)

        try:
            async with self._session.get(
                url,
                timeout=20,
            ) as response:
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
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

        now = datetime.now(UTC)

        if (
            self._xml_cache
            and self._xml_cache_time
            and (now - self._xml_cache_time) < timedelta(minutes=15)
        ):
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
            try:
                async with self._session.get(
                    url, headers=headers, timeout=5
                ) as response:
                    if response.status == 200:
                        xml_text = await response.text()
                        if not xml_text.strip().startswith(("<!DOCTYPE", "<html")):
                            self._xml_cache = xml_text
                            self._xml_cache_time = now

                            forecasts = parse_osmer_forecast_xml(xml_text, zone)
                            if forecasts:
                                return forecasts
            except (
                aiohttp.ClientError,
                OsmerApiError,
                UnicodeDecodeError,
            ) as err:
                _LOGGER.debug("Error fetching XML forecast from %s: %s", url, err)

        return []
