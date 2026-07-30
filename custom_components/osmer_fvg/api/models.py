"""Models for the OSMER API."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Station:
    """Weather station."""

    id: int
    name: str
    istat: int
    latitude: float
    longitude: float
    elevation: int
    status: str