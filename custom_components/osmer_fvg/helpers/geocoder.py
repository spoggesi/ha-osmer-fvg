"""Nominatim geocoder helper."""

from __future__ import annotations

import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)


class NominatimGeocoder:
    """Wrapper around the Nominatim API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the geocoder."""

        self._session = session

    async def geocode(
        self,
        address: str,
    ) -> tuple[float, float] | None:
        """Return latitude and longitude."""

        query = (
            f"{address}, "
            "Friuli Venezia Giulia, Italia"
        )

        params = {
            "q": query,
            "format": "jsonv2",
            "limit": 1,
        }

        headers = {
            "User-Agent": "HomeAssistant-OSMER-FVG",
        }

        _LOGGER.debug(
            "Searching address: %s",
            query,
        )

        try:
            async with self._session.get(
                NOMINATIM_URL,
                params=params,
                headers=headers,
                timeout=20,
            ) as response:

                response.raise_for_status()

                results = await response.json()

        except aiohttp.ClientError as err:

            _LOGGER.error(
                "Geocoder error: %s",
                err,
            )

            return None

        if not results:
            return None

        result = results[0]

        return (
            float(result["lat"]),
            float(result["lon"]),
        )