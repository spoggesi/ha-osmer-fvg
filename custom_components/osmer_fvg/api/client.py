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
        """Initialize the API client."""
        self._session = session

    async def _get(self, endpoint: str) -> dict[str, Any]:
        """Execute a GET request."""

        url = f"{BASE_URL}{endpoint}"

        _LOGGER.debug("GET %s", url)

        try:
            async with self._session.get(url, timeout=20) as response:
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
            raise OsmerConnectionError(
                f"Unable to connect to {url}"
            ) from err

    async def get_stations(self) -> list[Station]:
        """Return all available weather stations."""

        data = await self._get("/stations")

        if data.get("result") != "OK":
            raise OsmerApiResponseError(
                f"Unexpected API response: {data.get('result')}"
            )

        stations = data.get("stations")

        if stations is None:
            raise OsmerApiResponseError(
                "Response does not contain 'stations'"
            )

        return [
            parse_station(station)
            for station in stations
        ]