"""Tests for OSMER persistent cache."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from custom_components.osmer_fvg.api.models import (
    Sensor,
    Station,
)
from custom_components.osmer_fvg.flow.cache import (
    CACHE_VERSION,
    OsmerCache,
)


async def test_cache_save_and_load(
    hass,
) -> None:
    """Test cache persistence."""

    cache = OsmerCache(
        hass,
    )


    cache.data = {
        "test": "value",
    }


    cache.store.async_save = AsyncMock()


    await cache.async_save()


    cache.store.async_save.assert_called_once()


    saved_data = (
        cache.store.async_save
        .call_args
        .args[0]
    )


    assert saved_data["test"] == "value"

    assert saved_data["version"] == CACHE_VERSION

    assert "updated" in saved_data





async def test_cache_expired() -> None:
    """Test expired cache."""

    hass = MagicMock()


    cache = OsmerCache(
        hass,
    )


    cache.data = {
        "version": CACHE_VERSION,
        "updated": (
            datetime.now(
                timezone.utc,
            )
            -
            timedelta(
                days=31,
            )
        ).isoformat(),
    }


    assert cache.is_expired() is True





async def test_cache_not_expired() -> None:
    """Test valid cache."""

    hass = MagicMock()


    cache = OsmerCache(
        hass,
    )


    cache.data = {
        "version": CACHE_VERSION,
        "updated": datetime.now(
            timezone.utc,
        ).isoformat(),
    }


    assert cache.is_expired() is False





def test_cache_sensor_storage() -> None:
    """Test sensor cache."""

    hass = MagicMock()


    cache = OsmerCache(
        hass,
    )


    sensor = Sensor(
        id=1,
        station_id=51,
        code="T",
        name="Temperatura",
        decimals=1,
        unit="°C",
        status="O",
    )


    cache.set_sensors(
        51,
        [
            sensor,
        ],
    )


    assert cache.has_sensors(
        51,
    ) is True


    sensors = cache.get_sensors(
        51,
    )


    assert len(sensors) == 1

    assert sensors[0].code == "T"





def test_cache_sensor_missing() -> None:
    """Test missing sensor cache."""

    hass = MagicMock()


    cache = OsmerCache(
        hass,
    )


    assert cache.has_sensors(
        999,
    ) is False


    sensors = cache.get_sensors(
        999,
    )


    assert sensors == []





def test_cache_station_storage() -> None:
    """Test station cache."""

    hass = MagicMock()


    cache = OsmerCache(
        hass,
    )


    station = Station(
        id=51,
        name="Dignano",
        istat=30032,
        latitude=46.084672,
        longitude=12.930306,
        altitude=112,
        status="N",
    )


    cache.set_stations(
        [
            station,
        ],
    )


    stations = cache.get_stations()


    assert len(stations) == 1

    assert stations[0].name == "Dignano"





def test_cache_station_ids() -> None:
    """Test station id extraction."""

    hass = MagicMock()


    cache = OsmerCache(
        hass,
    )


    cache.data = {
        "stations": [
            {
                "id": 51,
                "name": "Dignano",
                "istat": 30032,
                "latitude": 46.084672,
                "longitude": 12.930306,
                "altitude": 112,
                "status": "N",
            }
        ]
    }


    ids = cache.get_station_ids()


    assert ids == {
        51,
    }