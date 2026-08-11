"""Search OSMER stations by name."""

import asyncio
import sys
from pathlib import Path

import aiohttp

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from custom_components.osmer_fvg.api.client import OsmerApiClient

SEARCH_QUERY = "pordenone"  # Cambia qui il nome della città da cercare


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        client = OsmerApiClient(session)
        stations = await client.get_stations()

        matches = [s for s in stations if SEARCH_QUERY.lower() in s.name.lower()]

        print("=" * 60)
        print(f"STAZIONI TROVATE PER '{SEARCH_QUERY}': {len(matches)}")
        print("=" * 60)

        for s in matches:
            print(
                f"ID: {s.id:<5} | Nome: {s.name:<25} | Lat: {s.latitude} | Lon: {s.longitude}"
            )


if __name__ == "__main__":
    asyncio.run(main())
