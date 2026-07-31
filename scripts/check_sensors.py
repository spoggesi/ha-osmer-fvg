"""Export all available OSMER sensors."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import aiofiles
import aiohttp

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from custom_components.osmer_fvg.api.client import OsmerApiClient
from custom_components.osmer_fvg.api.exceptions import (
    OsmerApiResponseError,
    OsmerConnectionError,
)

# Cambia qui la stazione da analizzare
STATION_ID = 209

OUTPUT_FILE = "osmer_available_sensors.json"


async def main() -> None:
    """Export sensors."""

    print("=" * 70)
    print("OSMER SENSOR EXPORT")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:

        client = OsmerApiClient(
            session,
        )

        try:
            sensors = await client.get_sensors(
                STATION_ID,
            )

        except (
            OsmerApiResponseError,
            OsmerConnectionError,
        ) as err:

            print(
                f"Errore recupero sensori: {err}"
            )

            return

        exported: list[dict[str, str]] = []

        seen: set[str] = set()

        for sensor in sensors:

            if sensor.code in seen:
                continue

            seen.add(
                sensor.code,
            )

            exported.append(
                {
                    "code": sensor.code,
                    "name": sensor.name,
                    "unit": sensor.unit,
                }
            )

        exported.sort(
            key=lambda item: item["code"],
        )

    async with aiofiles.open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        await file.write(
            json.dumps(
                exported,
                indent=2,
                ensure_ascii=False,
            )
        )

    print()
    print(
        f"Sensori trovati: {len(exported)}"
    )

    print()

    for sensor in exported:

        print(
            f'{sensor["code"]:20} | '
            f'{sensor["name"]:40} | '
            f'{sensor["unit"]}'
        )

    print()

    print(
        f"Creato file: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    asyncio.run(main())