"""Client for the OSMER FVG API."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .exceptions import (
    OsmerApiResponseError,
    OsmerConnectionError,
)
from .models import Station
from .parser import parse_station

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

        self._headers = {
            "User-Agent": "HomeAssistant-OSMER-FVG",
            "Accept": "application/json",
        }


    async def _get(
        self,
        endpoint: str,
    ) -> dict[str, Any]:
        """Execute GET request."""

        url = f"{BASE_URL}{endpoint}"

        _LOGGER.debug(
            "GET %s",
            url,
        )

        try:
            async with self._session.get(
                url,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:

                response.raise_for_status()

                data = await response.json()

                _LOGGER.debug(
                    "Response received from %s",
                    endpoint,
                )

                return data


        except aiohttp.ClientError as err:
            raise OsmerConnectionError(
                f"Unable to connect to {url}"
            ) from err


    async def get_stations(self) -> list[Station]:
        """Return all weather stations."""

        data = await self._get(
            "/stations"
        )


        if data.get("result") != "OK":
            raise OsmerApiResponseError(
                f"Unexpected result: {data.get('result')}"
            )


        stations = data.get(
            "stations"
        )

        if stations is None:
            raise OsmerApiResponseError(
                "Missing stations"
            )


        return [
            parse_station(item)
            for item in stations
        ]


    async def get_station(
        self,
        station_id: int,
    ) -> Station:
        """Return single station."""

        data = await self._get(
            f"/stations/{station_id}"
        )


        if data.get("result") != "OK":
            raise OsmerApiResponseError(
                "Invalid station response"
            )


        station = data.get(
            "station"
        )

        if station is None:
            raise OsmerApiResponseError(
                "Missing station"
            )


        return parse_station(
            station
        )