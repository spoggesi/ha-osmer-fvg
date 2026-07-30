"""OSMER FVG API discovery tool."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import aiohttp

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(
    0,
    str(ROOT_DIR),
)


from custom_components.osmer_fvg.api.client import OsmerApiClient

TEST_ENDPOINTS = [
    "/stations/{id}",
    "/station/{id}",
    "/observations/{id}",
    "/observations?station={id}",
    "/weather/{id}",
    "/data/{id}",
]


async def main() -> None:
    """Run API check."""

    print("=" * 70)
    print("OSMER FVG API CHECK")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:

        client = OsmerApiClient(
            session
        )

        stations = await client.get_stations()

        print(
            f"\nFound {len(stations)} stations\n"
        )

        print("=" * 70)
        print("FIRST 10 STATIONS")
        print("=" * 70)

        for station in stations[:10]:
            print(
                station
            )

        station = stations[0]

        print("\n")
        print("=" * 70)
        print("SELECTED STATION")
        print("=" * 70)

        print(
            station
        )

        print("\n")
        print("=" * 70)
        print("RAW STATION OBJECT")
        print("=" * 70)

        print(
            json.dumps(
                station.__dict__,
                indent=4,
            )
        )

        print("\n")
        print("=" * 70)
        print("ENDPOINT DISCOVERY")
        print("=" * 70)

        for endpoint in TEST_ENDPOINTS:

            endpoint_path = endpoint.format(
                id=station.id
            )

            url = (
                "https://monitor.protezionecivile.fvg.it/api"
                + endpoint_path
            )

            print(
                f"\nTesting: {endpoint_path}"
            )

            try:
                async with session.get(
                    url
                ) as response:

                    print(
                        "Status:",
                        response.status,
                    )

                    print(
                        "Content-Type:",
                        response.headers.get(
                            "content-type"
                        ),
                    )

                    if response.status == 200:

                        try:
                            data = await response.json()

                            print(
                                json.dumps(
                                    data,
                                    indent=4,
                                )[:1000]
                            )

                        except aiohttp.ContentTypeError:
                            print(
                                await response.text()
                            )

            except aiohttp.ClientError as err:

                print(
                    "HTTP ERROR:",
                    err,
                )


if __name__ == "__main__":
    asyncio.run(main())