"""Client for the OSMER FVG API."""

from __future__ import annotations

import aiohttp

from .exceptions import OsmerConnectionError

BASE_URL = "https://monitor.protezionecivile.fvg.it/api"


class OsmerApiClient:
    """Client for the OSMER API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
    ) -> None:
        self._session = session

    async def _get(self, endpoint: str):
        """Execute a GET request."""

        url = f"{BASE_URL}{endpoint}"

        try:
            async with self._session.get(url, timeout=20) as response:
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
            raise OsmerConnectionError from err