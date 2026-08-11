"""XML Parser for OSMER FVG dev bulletin XML."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

from ..const import map_osmer_condition
from .models import OsmerForecastDay

_LOGGER = logging.getLogger(__name__)


def _parse_date(date_str: str) -> str:
    """Convert DD-MM-YYYY or DD/MM/YYYY to ISO YYYY-MM-DD."""
    date_str = date_str.strip()
    sep = "-" if "-" in date_str else ("/" if "/" in date_str else None)
    if sep:
        parts = date_str.split(sep)
        if len(parts) == 3:
            if len(parts[0]) == 2 and len(parts[2]) == 4:
                return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            if len(parts[0]) == 4:
                return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
    return date_str


def parse_osmer_forecast_xml(
    xml_content: str,
    target_zone: str,
) -> list[OsmerForecastDay]:
    """Parse OSMER dev XML bulletin for the given forecast zone."""

    forecasts: list[OsmerForecastDay] = []
    clean_content = xml_content.strip()

    if clean_content.startswith(("<!DOCTYPE", "<html")):
        _LOGGER.debug("Received HTML response instead of XML")
        return forecasts

    try:
        root = ET.fromstring(clean_content)
    except ET.ParseError as err:
        _LOGGER.warning("Failed to parse OSMER XML bulletin: %s", err)
        return forecasts

    clean_target = str(target_zone).strip().upper().replace("Z", "")
    scadenze = root.findall(".//scadenza")

    for scadenza in scadenze:
        raw_date = scadenza.attrib.get("data_validita", "").strip()
        if not raw_date:
            continue

        iso_date = _parse_date(raw_date)

        # Trova il nodo <zona> corrispondente a target_zone
        zona_node = None
        for z in scadenza.findall(".//zona"):
            z_nome = z.attrib.get("nome", "").strip().upper().replace("Z", "")
            z_id = z.attrib.get("id", "").strip().upper().replace("Z", "")
            if z_nome == clean_target or z_id == clean_target:
                zona_node = z
                break

        if zona_node is None:
            continue

        cond_text = (
            zona_node.findtext("EVOLUZIONE12_DESCRIZIONE")
            or zona_node.findtext("EVOLUZIONE24_DESCRIZIONE")
            or zona_node.findtext("EVOLUZIONE00_DESCRIZIONE")
            or zona_node.findtext("TESTO")
            or ""
        )
        condition = map_osmer_condition(cond_text)
        summary = zona_node.findtext("TESTO") or cond_text or None

        temp_min: float | None = None
        temp_max: float | None = None

        for elem in list(zona_node) + list(scadenza):
            tag_upper = elem.tag.upper()
            val_text = elem.text.strip() if elem.text else ""
            if not val_text:
                continue

            try:
                val_float = float(val_text)
            except ValueError:
                continue

            if ("TMIN" in tag_upper or "MIN" in tag_upper) and temp_min is None:
                temp_min = val_float
            elif ("TMAX" in tag_upper or "MAX" in tag_upper) and temp_max is None:
                temp_max = val_float

        forecasts.append(
            OsmerForecastDay(
                date=iso_date,
                condition=condition,
                temp_min=temp_min,
                temp_max=temp_max,
                precipitation_probability=None,
                summary=summary,
            )
        )

    return forecasts
