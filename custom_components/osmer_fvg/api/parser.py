"""Parsers for OSMER FVG API."""

from __future__ import annotations

from datetime import datetime, timezone

from .models import Measure, Sensor, Station


def parse_station(data: dict) -> Station:
    """Parse station data from API."""

    return Station(
        id=data["id"],
        name=data["name"],
        istat=data["istat"],
        latitude=data["lat"],
        longitude=data["lon"],
        altitude=data["alt"],
        status=data["status"],
    )


def parse_sensor(data: dict) -> Sensor:
    """Parse sensor data from API."""

    return Sensor(
        id=data["id"],
        station_id=data["station_id"],
        code=data["code"],
        name=data["name"],
        decimals=data["decimals"],
        unit=data["unit"],
        status=data["status"],
    )


def parse_measure(data: dict) -> Measure:
    """Parse measurement data."""

    timestamp = datetime.strptime(
        data["dt"],
        "%Y-%m-%d %H:%M:%S",
    ).replace(
        tzinfo=timezone.utc,
    )

    return Measure(
        station_id=data["station_id"],
        sensor_id=data["sensor_id"],
        timestamp=timestamp,
        latitude=data["lat"],
        longitude=data["lon"],
        value=data["value"],
    )
