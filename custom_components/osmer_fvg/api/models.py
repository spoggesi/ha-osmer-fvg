"""Models for OSMER FVG API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Station:
    """Weather station information."""

    id: int
    name: str
    istat: int
    latitude: float
    longitude: float
    altitude: float
    status: str

    def __str__(self) -> str:
        """Return human readable representation."""
        return (
            f"{self.name} "
            f"(ID {self.id}) "
            f"{self.latitude:.5f}, "
            f"{self.longitude:.5f} "
            f"{self.altitude:.1f}m"
        )


@dataclass(frozen=True)
class Observation:
    """Weather observation."""

    station_id: int
    timestamp: datetime

    temperature: float | None = None
    humidity: float | None = None
    pressure: float | None = None

    wind_speed: float | None = None
    wind_direction: float | None = None

    rain: float | None = None


@dataclass(frozen=True)
class Forecast:
    """Weather forecast."""

    station_id: int
    timestamp: datetime

    temperature: float | None = None
    rain_probability: float | None = None