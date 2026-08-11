"""XML Parser for OSMER FVG official bulletin."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

from ..const import map_osmer_condition
from .models import OsmerForecastDay

_LOGGER = logging.getLogger(__name__)


def parse_osmer_forecast_xml(
    xml_content: str,
    target_zone: str,
) -> list[OsmerForecastDay]:
    """Parse OSMER XML bulletin for the given forecast zone."""

    forecasts: list[OsmerForecastDay] = []

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as err:
        _LOGGER.warning("Failed to parse OSMER XML bulletin: %s", err)
        return forecasts

    # Cicla sui giorni previsionali presenti nel bollettino XML
    for giorno_elem in root.findall(".//giorno"):
        date_str = giorno_elem.findtext("data", "").strip()

        if not date_str:
            continue

        # Cerca i dati specifici della macro-zona target (Z1, Z2, Z3, Z4)
        zona_elem = None
        for z in giorno_elem.findall(".//zona"):
            if z.get("id") == target_zone or z.findtext("id") == target_zone:
                zona_elem = z
                break

        # Fallback sugli elementi generali del giorno se la zona non è specificata
        node = zona_elem if zona_elem is not None else giorno_elem

        condition_raw = (
            node.findtext("simbolo", "")
            or node.findtext("cielo", "")
            or giorno_elem.findtext("simbolo", "")
        )

        condition = map_osmer_condition(condition_raw)

        t_min_str = node.findtext("tmin") or giorno_elem.findtext("tmin")
        t_max_str = node.findtext("tmax") or giorno_elem.findtext("tmax")

        try:
            temp_min = float(t_min_str) if t_min_str is not None else None
        except ValueError:
            temp_min = None

        try:
            temp_max = float(t_max_str) if t_max_str is not None else None
        except ValueError:
            temp_max = None

        precip_str = node.findtext("prob_precip") or giorno_elem.findtext("prob_precip")

        try:
            precip_prob = int(precip_str) if precip_str is not None else None
        except ValueError:
            precip_prob = None

        summary = (
            node.findtext("testo")
            or node.findtext("evoluzione")
            or giorno_elem.findtext("testo")
        )

        forecasts.append(
            OsmerForecastDay(
                date=date_str,
                condition=condition,
                temp_min=temp_min,
                temp_max=temp_max,
                precipitation_probability=precip_prob,
                summary=summary,
            )
        )

    return forecasts
