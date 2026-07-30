"""Check available OSMER sensors and latest values."""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from custom_components.osmer_fvg.api.client import OsmerApiClient
from custom_components.osmer_fvg.api.exceptions import (
    OsmerApiResponseError,
    OsmerConnectionError,
)

STATION_ID = 209


async def main() -> None:
    """Run sensor check."""

    print("=" * 70)
    print("OSMER SENSOR CHECK")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:
        client = OsmerApiClient(session)

        sensors = await client.get_sensors(STATION_ID)

        print()
        print("AVAILABLE SENSORS")
        print("-" * 70)

        for sensor in sensors:
            print(
                f"{sensor.id:3} | {sensor.code:12} | {sensor.name:35} | {sensor.unit}"
            )

        print()
        print("=" * 70)
        print("LATEST VALUES")
        print("=" * 70)

        now = datetime.now(timezone.utc)

        start = now - timedelta(hours=3)

        for sensor in sensors:
            try:
                measures = await client.get_measures(
                    station_id=STATION_ID,
                    sensor_id=sensor.id,
                    start=start.isoformat(),
                    end=now.isoformat(),
                )

                if not measures:
                    print(f"{sensor.code:12} -> NO DATA")
                    continue

                latest = measures[-1]

                print(
                    f"{sensor.code:12} -> "
                    f"{latest.value} {sensor.unit} "
                    f"({latest.timestamp})"
                )

            except (
                OsmerApiResponseError,
                OsmerConnectionError,
                aiohttp.ClientError,
            ) as err:
                print(f"{sensor.code:12} -> ERROR {err}")


if __name__ == "__main__":
    asyncio.run(main())
