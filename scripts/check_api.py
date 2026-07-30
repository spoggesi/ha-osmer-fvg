"""OSMER API discovery script."""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


from custom_components.osmer_fvg.api.client import OsmerApiClient

STATION_ID = 209
TEMPERATURE_SENSOR_ID = 2


async def main() -> None:
    """Run API check."""

    print("=" * 70)
    print("OSMER FVG API DISCOVERY")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:
        client = OsmerApiClient(session)

        stations = await client.get_stations()

        station = next(s for s in stations if s.id == STATION_ID)

        print("\nSTATION")
        print("-" * 70)
        print(station)

        sensors = await client.get_sensors(STATION_ID)

        print("\nSENSORS")
        print("-" * 70)

        for sensor in sensors:
            print(
                f"{sensor.id:3} | {sensor.code:12} | {sensor.name:30} | {sensor.unit}"
            )

        end = datetime.now(timezone.utc)

        start = end - timedelta(hours=3)

        print("\nTEMPERATURE LAST MEASURES")
        print("-" * 70)

        measures = await client.get_measures(
            station_id=STATION_ID,
            sensor_id=TEMPERATURE_SENSOR_ID,
            start=start.isoformat(),
            end=end.isoformat(),
        )

        for measure in measures[-10:]:
            print(
                measure.timestamp,
                measure.value,
            )


if __name__ == "__main__":
    asyncio.run(main())
