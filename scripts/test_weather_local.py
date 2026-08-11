"""Local test script for OSMER weather forecast logic."""

import asyncio
import os
import sys

# Aggiunge la cartella radice del workspace al percorso dei moduli Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import aiohttp

from custom_components.osmer_fvg.api.client import OsmerApiClient
from custom_components.osmer_fvg.weather import OsmerWeatherEntity


class MockCoordinator:
    """Mock coordinator for local testing."""

    def __init__(self, station, forecasts, measures):
        self.data = type(
            "OsmerData",
            (),
            {
                "station": station,
                "forecasts": forecasts,
                "measures": measures,
            },
        )()


async def main() -> None:
    """Run local forecast check."""
    async with aiohttp.ClientSession() as session:
        client = OsmerApiClient(session)

        print("1. Scarico stazioni dall'API...")
        stations = await client.get_stations()
        station = stations[0]
        print(f"   Stazione selezionata: {station.name} (ID: {station.id})")

        print("\n2. Scarico previsioni per la Zona Z3...")
        forecasts = await client.get_forecasts("Z3")
        print(f"   Trovati {len(forecasts)} giorni di previsione:")
        for f in forecasts:
            print(
                f"   - Data: {f.date} | Condizione: {f.condition} | T.Min: {f.temp_min}°C | T.Max: {f.temp_max}°C"
            )

        print("\n3. Verifico formattazione per la Scheda Meteo di Home Assistant...")
        mock_coordinator = MockCoordinator(station, forecasts, {})
        weather_entity = OsmerWeatherEntity(mock_coordinator)

        ha_payload = weather_entity._get_forecast_list()
        print("   Payload inviato al Frontend:")
        import pprint

        pprint.pprint(ha_payload)


if __name__ == "__main__":
    asyncio.run(main())
