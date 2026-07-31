"""Helpers for loading OSMER stations and sensors."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)

from ..api.client import OsmerApiClient
from ..api.models import Sensor, Station


class FlowLoader:
    """Load data required by the config flow."""

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""

        self._hass = hass

        self._client: OsmerApiClient | None = None

        self._sensor_cache: dict[
            int,
            list[Sensor],
        ] = {}

    @property
    def client(
        self,
    ) -> OsmerApiClient:
        """Return API client."""

        if self._client is None:

            self._client = OsmerApiClient(
                async_get_clientsession(
                    self._hass,
                )
            )

        return self._client

    async def get_stations(
        self,
    ) -> list[Station]:
        """Return all stations."""

        stations = await self.client.get_stations()

        return sorted(
            stations,
            key=lambda station: station.name.casefold(),
        )

    async def get_station(
        self,
        station_id: int,
    ) -> Station | None:
        """Return station."""

        stations = await self.get_stations()

        for station in stations:

            if station.id == station_id:

                return station

        return None

    async def get_sensors(
        self,
        station: Station,
    ) -> list[Sensor]:
        """Return sensors for station."""

        if station.id in self._sensor_cache:

            return self._sensor_cache[
                station.id
            ]

        sensors = await self.client.get_sensors(
            station.id,
        )

        sensors = sorted(
            sensors,
            key=lambda sensor: sensor.name.casefold(),
        )

        self._sensor_cache[
            station.id
        ] = sensors

        return sensors

    async def preload(
        self,
        stations: list[Station],
    ) -> None:
        """Populate sensor cache."""

        for station in stations:

            await self.get_sensors(
                station,
            )