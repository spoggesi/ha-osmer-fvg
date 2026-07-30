"""Models for OSMER FVG API."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    """Weather station information."""

    id: int
    name: str
    istat: int
    latitude: float
    longitude: float
    altitude: int
    status: str
