"""Simple script to test the OSMER API client."""

import asyncio
import sys
from pathlib import Path

import aiohttp

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from custom_components.osmer_fvg.api.client import OsmerApiClient


async def main() -> None:
    """Run the test."""

    async with aiohttp.ClientSession() as session:
        client = OsmerApiClient(session)

        stations = await client.get_stations()

        print(f"Found {len(stations)} stations\n")

        for station in stations[:10]:
            print(station)


if __name__ == "__main__":
    asyncio.run(main())