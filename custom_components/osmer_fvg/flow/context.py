"""Shared state for the OSMER config flow."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..api.models import Sensor, Station


@dataclass(slots=True)
class FlowContext:
    """Shared data used by the config flow."""

    #
    # Selection method
    #
    # "address" -> search by address
    # "station" -> select from station list
    #
    selection_method: str | None = None

    #
    # Stations
    #
    stations: list[Station] = field(
        default_factory=list,
    )

    #
    # Selected station
    #
    station: Station | None = None

    #
    # Sensors of selected station
    #
    sensors: list[Sensor] = field(
        default_factory=list,
    )

    #
    # Enabled sensors chosen by user
    #
    enabled_sensors: list[str] = field(
        default_factory=list,
    )

    #
    # Cache:
    # station_id -> sensors
    #
    sensor_cache: dict[int, list[Sensor]] = field(
        default_factory=dict,
    )

    #
    # Address entered by user
    #
    address: str | None = None

    #
    # Coordinates returned by Nominatim
    #
    latitude: float | None = None

    longitude: float | None = None

    #
    # Nearest stations
    #
    nearest: list[Station] = field(
        default_factory=list,
    )

    def clear_selection(self) -> None:
        """Reset selected station."""

        self.station = None

        self.sensors.clear()

        self.enabled_sensors.clear()

    def clear_address(self) -> None:
        """Reset address search."""

        self.address = None

        self.latitude = None

        self.longitude = None

        self.nearest.clear()

    def reset(self) -> None:
        """Reset complete flow context."""

        self.selection_method = None

        self.stations.clear()

        self.clear_selection()

        self.sensor_cache.clear()

        self.clear_address()