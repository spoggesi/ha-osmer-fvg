"""Service layer used by the config flow."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)

from ..api.client import OsmerApiClient
from ..api.models import Sensor, Station
from ..helpers.distance import distance_km
from ..helpers.geocoder import (
    NominatimGeocoder,
)
from .context import FlowContext
from .loader import FlowLoader


class FlowService:
    """Service used by the config flow."""

    def __init__(
        self,
        hass: HomeAssistant,
        context: FlowContext,
    ) -> None:
        """Initialize."""

        self._context = context

        self._loader = FlowLoader(
            hass,
        )

        self._geocoder = NominatimGeocoder(
            async_get_clientsession(
                hass,
            )
        )

    @property
    def client(
        self,
    ) -> OsmerApiClient:
        """Return API client."""

        return self._loader.client

    async def load_stations(
        self,
    ) -> list[Station]:
        """Load all stations."""

        stations = await self._loader.get_stations()

        self._context.stations = stations

        return stations

    async def load_station(
        self,
        station_id: int,
    ) -> Station | None:
        """Return station by id."""

        station = await self._loader.get_station(
            station_id,
        )

        self._context.station = station

        return station

    async def load_sensors(
        self,
        station: Station,
    ) -> list[Sensor]:
        """Load station sensors."""

        sensors = await self._loader.get_sensors(
            station,
        )

        self._context.station = station

        self._context.sensors = sensors

        self._context.enabled_sensors = [
            sensor.code
            for sensor in sensors
        ]

        return sensors

    async def search_address(
        self,
        address: str,
    ) -> tuple[float, float] | None:
        """Search an address."""

        result = await self._geocoder.geocode(
            address,
        )

        if result is None:
            return None

        latitude, longitude = result

        self._context.address = address
        self._context.latitude = latitude
        self._context.longitude = longitude

        return result

    def nearest_stations(
        self,
        limit: int = 5,
    ) -> list[Station]:
        """Return nearest stations."""

        if (
            self._context.latitude is None
            or self._context.longitude is None
        ):
            return []

        stations = sorted(
            self._context.stations,
            key=lambda station: distance_km(
                self._context.latitude,
                self._context.longitude,
                station.latitude,
                station.longitude,
            ),
        )

        stations = stations[:limit]

        self._context.nearest = stations

        return stations

    async def preload(self) -> None:
        """Preload sensors."""

        await self._loader.preload(
            self._context.stations,
        )