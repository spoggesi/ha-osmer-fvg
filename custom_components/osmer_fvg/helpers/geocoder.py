"""Nominatim geocoder helper."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from ..logging import reset_request_id, set_request_id

_LOGGER = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_GEOCODE_TIMEOUT = 20  # seconds


class NominatimGeocoder:
    """Wrapper around the Nominatim API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        timeout: int = DEFAULT_GEOCODE_TIMEOUT,
    ) -> None:
        """Initialize the geocoder."""

        self._session = session
        self._timeout = timeout

    async def geocode(
        self,
        address: str,
    ) -> tuple[float, float] | None:
        """Return latitude and longitude."""
        set_request_id()

        query = f"{address}, Friuli Venezia Giulia, Italia"

        params: dict[str, Any] = {
            "q": query,
            "format": "jsonv2",
            "limit": 1,
        }

        headers = {
            "User-Agent": "HomeAssistant-OSMER-FVG",
        }

        _LOGGER.info(
            "Searching address: %s",
            query,
        )

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(
                    NOMINATIM_URL,
                    params=params,
                    headers=headers,
                    timeout=self._timeout,
                ) as response:
                    response.raise_for_status()

                    results = await response.json()
                    reset_request_id()

        except (TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error(
                "Geocoder connection error for '%s': %s",
                query,
                err,
            )
            reset_request_id()
            return None
        except Exception as err:  # noqa: BLE001
            _LOGGER.error(
                "Geocoder unexpected error for '%s': %s (type: %s)",
                query,
                err,
                type(err).__name__,
            )
            reset_request_id()
            return None

        if not results:
            _LOGGER.debug(
                "No geocoding results for: %s",
                query,
            )
            reset_request_id()
            return None

        result = results[0]

        lat = float(result["lat"])
        lon = float(result["lon"])

        _LOGGER.debug(
            "Geocoding successful: %s -> (%s, %s)",
            address,
            lat,
            lon,
        )
        reset_request_id()

        return (lat, lon)
