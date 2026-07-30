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
            f"{self.altitude}m"
        )


@dataclass(frozen=True)
class Sensor:
    """Weather sensor information."""

    id: int
    station_id: int

    code: str
    name: str

    decimals: int
    unit: str

    status: str

    @property
    def device_class(self) -> str | None:
        """Return Home Assistant device class."""

        mapping = {
            "T": "temperature",
            "U": "humidity",
            "P": "precipitation",
            "RR": "precipitation",
            "IDRO": "water",
        }

        return mapping.get(self.code)


@dataclass(frozen=True)
class Measure:
    """Sensor measurement."""

    station_id: int
    sensor_id: int

    timestamp: datetime

    latitude: float
    longitude: float

    value: float | None
