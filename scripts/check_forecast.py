"""OSMER forecast verification script."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import aiohttp

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from custom_components.osmer_fvg.api.client import OsmerApiClient
from custom_components.osmer_fvg.forecast_zone import get_osmer_zone

logging.basicConfig(level=logging.INFO)

STATION_ID = 209


async def main() -> None:
    """Run forecast verification."""

    print("=" * 70)
    print("OSMER FVG FORECAST VERIFICATION")
    print("=" * 70)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HomeAssistant-OSMER-FVG"
        )
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        client = OsmerApiClient(session)

        print(f"\n1. RECUPERO STAZIONE (ID: {STATION_ID})...")
        station = await client.get_station(STATION_ID)
        print(f"Stazione: {station}")

        zone = get_osmer_zone(
            station.latitude,
            station.longitude,
            station.altitude,
        )

        print(f"\n2. MACRO-ZONA CALCOLATA: {zone}")
        print("-" * 70)

        print(f"\n3. RECUPERO PREVISIONI PER MACRO-ZONA {zone}...")
        forecasts = await client.get_forecasts(zone)

        print("-" * 70)
        if not forecasts:
            print("❌ Nessuna previsione estratta.")
            return

        print(f"✅ Estratti {len(forecasts)} giorni di previsione:\n")
        for f in forecasts:
            print(f"📅 Data (ISO): {f.date}")
            print(f"   Condizione HA: {f.condition}")
            if f.temp_min is not None or f.temp_max is not None:
                print(f"   Temp Min/Max: {f.temp_min}°C / {f.temp_max}°C")
            if f.summary:
                print(f"   Sintesi: {f.summary}")
            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
