"""Tests for the OSMER API client."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp

from custom_components.osmer_fvg.api.client import OsmerApiClient


async def test_get_stations() -> None:
    """Test retrieving stations from the API."""

    response_data = {
        "result": "OK",
        "stations": [
            {
                "id": 51,
                "name": "Dignano",
                "istat": 30032,
                "lat": 46.084672,
                "lon": 12.930306,
                "alt": 112,
                "status": "N",
            }
        ],
    }

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value=response_data)

    session = MagicMock(spec=aiohttp.ClientSession)

    session.get.return_value.__aenter__.return_value = mock_response

    client = OsmerApiClient(session)

    stations = await client.get_stations()

    assert len(stations) == 1

    station = stations[0]

    assert station.id == 51
    assert station.name == "Dignano"
    assert station.latitude == 46.084672
    assert station.longitude == 12.930306