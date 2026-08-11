"""API client for OSMER FVG weather data."""

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
from .models import OsmerForecastDay, Sensor, Station
from .xml_parser import parse_osmer_forecast_xml

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://www.meteo.fvg.it/xml"


class OsmerApiClient:
    """Client for OSMER FVG API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize API client."""
        self._session = session
        self._xml_cache: str | None = None
        self._xml_cache_time: datetime | None = None

    async def _get_json(self, url: str) -> Any:
        """Fetch JSON data from URL."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HomeAssistant-OSMER-FVG"
            )
        }
        try:
            async with self._session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    raise OsmerApiResponseError(f"HTTP status error: {response.status}")
                return await response.json()
        except aiohttp.ClientError as err:
            raise OsmerConnectionError(
                f"Connection error fetching {url}: {err}"
            ) from err

    async def get_stations(self) -> list[Station]:
        """Return list of stations."""
        url = f"{BASE_URL}/stazioni.php"
        data = await self._get_json(url)

        stations: list[Station] = []
        for item in data:
            try:
                station = Station(
                    id=int(item.get("id_stazione") or item.get("id")),
                    name=str(item.get("nome_stazione") or item.get("name")),
                    latitude=float(item.get("latitudine") or item.get("lat")),
                    longitude=float(item.get("longitudine") or item.get("lon")),
                    altitude=float(item.get("quota") or item.get("alt")),
                    istat=int(item.get("istat", 0)),
                    status=str(item.get("status", "N")),
                )
                stations.append(station)
            except (KeyError, ValueError, TypeError) as err:
                _LOGGER.debug("Skipping invalid station data: %s", err)
                continue

        return stations

    async def get_station(self, station_id: int) -> Station:
        """Return specific station by ID."""
        stations = await self.get_stations()
        for station in stations:
            if station.id == station_id:
                return station
        raise OsmerApiError(f"Station ID {station_id} not found")

    async def get_sensors(self, station_id: int) -> list[Sensor]:
        """Return sensors for a given station."""
        url = f"{BASE_URL}/stazione.php?id={station_id}"
        data = await self._get_json(url)

        sensors: list[Sensor] = []
        sensor_list = data.get("sensori", [])
        for item in sensor_list:
            try:
                sensor = Sensor(
                    id=int(item["id_sensore"]),
                    code=item["codice_sensore"],
                    name=item["nome_sensore"],
                    unit=item.get("unita_misura", ""),
                )
                sensors.append(sensor)
            except (KeyError, ValueError) as err:
                _LOGGER.debug("Skipping invalid sensor data: %s", err)
                continue

        return sensors

    async def get_forecasts(self, zone: str) -> list[OsmerForecastDay]:
        """Return forecast for zone from OSMER dev XML bulletin with RAM cache."""
        now = datetime.now(UTC)

        # 1. Se l'XML è già in cache RAM ed è più recente di 15 minuti, usalo direttamente
        if (
            self._xml_cache
            and self._xml_cache_time
            and (now - self._xml_cache_time) < timedelta(minutes=15)
        ):
            forecasts = parse_osmer_forecast_xml(self._xml_cache, zone)
            if forecasts:
                return forecasts

        # 2. Altrimenti scarica il bollettino aggiornato
        dates_to_try = [
            now.strftime("%Y%m%d"),
            (now - timedelta(days=1)).strftime("%Y%m%d"),
            (now - timedelta(days=2)).strftime("%Y%m%d"),
        ]

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HomeAssistant-OSMER-FVG"
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
                            # Salva in cache RAM
                            self._xml_cache = xml_text
                            self._xml_cache_time = now

                            forecasts = parse_osmer_forecast_xml(xml_text, zone)
                            if forecasts:
                                return forecasts
            except (aiohttp.ClientError, OsmerApiError) as err:
                _LOGGER.debug("Error fetching forecast from %s: %s", url, err)

        return []
