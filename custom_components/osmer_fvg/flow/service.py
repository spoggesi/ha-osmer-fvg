"""Service layer used by the config flow."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)

from ..api.client import OsmerApiClient
from ..api.models import Sensor, Station
from ..helpers.distance import distance_km
from ..helpers.geocoder import NominatimGeocoder
from .cache import OsmerCache
from .context import FlowContext
from .loader import FlowLoader


class FlowService:
    """Service used by the config flow."""

    def __init__(
        self,
        hass: HomeAssistant,
        context: FlowContext,
        loader: FlowLoader,
    ) -> None:
        """Initialize."""

        self.hass = hass

        self._context = context

        self._loader = loader

        self._cache = OsmerCache(
            hass,
        )

        self._geocoder = NominatimGeocoder(
            async_get_clientsession(
                hass,
            )
        )



    async def async_init_cache(
        self,
    ) -> None:
        """Load persistent cache."""

        await self._cache.async_load()



    @property
    def client(
        self,
    ) -> OsmerApiClient:
        """Return API client."""

        return self._loader.client



    async def load_stations(
        self,
    ) -> list[Station]:
        """Load stations."""

        if not self._cache.is_expired():

            stations = self._cache.get_stations()

            if stations:

                self._context.stations = stations

                for station in stations:

                    sensors = self._cache.get_sensors(
                        station.id,
                    )

                    if sensors:

                        self._context.sensor_cache[
                            station.id
                        ] = sensors


                self._context.cache_loaded = True

                return stations



        stations = await self._loader.get_stations()


        self._context.stations = stations

        self._context.cache_expired = True


        return stations



    async def load_station(
        self,
        station_id: int,
    ) -> Station | None:
        """Load station."""

        station = await self._loader.get_station(
            station_id,
        )

        self._context.station = station

        return station



    async def load_sensors(
        self,
        station: Station,
    ) -> list[Sensor]:
        """Load sensors."""

        if station.id in self._context.sensor_cache:

            sensors = self._context.sensor_cache[
                station.id
            ]


        else:

            sensors = await self._loader.get_sensors(
                station,
            )


            self._context.sensor_cache[
                station.id
            ] = sensors



        self._context.station = station

        self._context.sensors = sensors


        return sensors



    async def preload(
        self,
    ) -> None:
        """Preload all sensors."""

        for station in self._context.stations:

            if station.id not in self._context.sensor_cache:

                sensors = await self._loader.get_sensors(
                    station,
                )


                self._context.sensor_cache[
                    station.id
                ] = sensors



        self._cache.set_stations(
            self._context.stations,
        )


        for station_id, sensors in self._context.sensor_cache.items():

            self._cache.set_sensors(
                station_id,
                sensors,
            )


        await self._cache.async_save()



    async def search_address(
        self,
        address: str,
    ) -> tuple[float, float] | None:
        """Search address."""

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