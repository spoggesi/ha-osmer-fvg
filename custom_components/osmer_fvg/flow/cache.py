"""Persistent cache manager for OSMER FVG."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..api.models import Sensor, Station

CACHE_VERSION = 1

CACHE_KEY = "osmer_fvg_cache"

CACHE_TTL_DAYS = 30



class OsmerCache:
    """Persistent cache handler."""



    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize cache."""

        self.store = Store(
            hass,
            CACHE_VERSION,
            CACHE_KEY,
        )


        self.data: dict[str, Any] = {}



    async def async_load(
        self,
    ) -> None:
        """Load cache from disk."""

        stored = await self.store.async_load()


        if stored:

            self.data = stored

        else:

            self.data = {}



    async def async_save(
        self,
    ) -> None:
        """Save cache."""

        self.update_timestamp()

        self.data["version"] = CACHE_VERSION


        await self.store.async_save(
            self.data,
        )



    def update_timestamp(
        self,
    ) -> None:
        """Update cache timestamp."""

        self.data["updated"] = (
            datetime.now(
                timezone.utc,
            )
            .isoformat()
        )



    def is_expired(
        self,
    ) -> bool:
        """Check if cache expired."""

        if (
            self.data.get(
                "version",
            )
            != CACHE_VERSION
        ):

            return True



        timestamp = self.data.get(
            "updated",
        )


        if not timestamp:

            return True



        updated = datetime.fromisoformat(
            timestamp,
        )


        return (
            datetime.now(
                timezone.utc,
            )
            -
            updated
            >
            timedelta(
                days=CACHE_TTL_DAYS,
            )
        )



    #
    # Stations
    #


    def get_stations(
        self,
    ) -> list[Station]:
        """Get cached stations."""

        stations = self.data.get(
            "stations",
            [],
        )


        return [
            Station(**station)
            for station in stations
        ]



    def set_stations(
        self,
        stations: list[Station],
    ) -> None:
        """Store stations."""

        self.data["stations"] = [
            station.__dict__
            for station in stations
        ]



    def get_station_ids(
        self,
    ) -> set[int]:
        """Return cached station ids."""

        return {
            station.id
            for station in self.get_stations()
        }



    #
    # Sensors
    #


    def get_sensors(
        self,
        station_id: int,
    ) -> list[Sensor]:
        """Get cached sensors."""

        sensors = (
            self.data
            .get(
                "sensors",
                {},
            )
            .get(
                str(station_id),
                [],
            )
        )


        return [
            Sensor(**sensor)
            for sensor in sensors
        ]



    def has_sensors(
        self,
        station_id: int,
    ) -> bool:
        """Check if station sensors exist."""

        return (
            str(station_id)
            in self.data.get(
                "sensors",
                {},
            )
        )



    def set_sensors(
        self,
        station_id: int,
        sensors: list[Sensor],
    ) -> None:
        """Store sensors."""

        if (
            "sensors"
            not in self.data
        ):

            self.data["sensors"] = {}



        self.data["sensors"][
            str(station_id)
        ] = [
            sensor.__dict__
            for sensor in sensors
        ]



    #
    # Utility
    #


    def clear(
        self,
    ) -> None:
        """Clear cache."""

        self.data = {}