"""Tests for the OSMER API parser."""

from custom_components.osmer_fvg.api.models import Station
from custom_components.osmer_fvg.api.parser import parse_station


def test_parse_station() -> None:
    """Test parsing a station."""

    data = {
        "id": 51,
        "name": "Dignano",
        "istat": 30032,
        "lat": 46.084672,
        "lon": 12.930306,
        "alt": 112,
        "status": "N",
    }

    station = parse_station(data)

    assert isinstance(station, Station)
    assert station.id == 51
    assert station.name == "Dignano"
    assert station.istat == 30032
    assert station.latitude == 46.084672
    assert station.longitude == 12.930306
    assert station.altitude == 112
    assert station.status == "N"