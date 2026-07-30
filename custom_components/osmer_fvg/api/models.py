from dataclasses import dataclass


@dataclass(slots=True)
class Station:
    """Weather station."""

    id: int
    name: str
    latitude: float
    longitude: float
    network: str | None = None