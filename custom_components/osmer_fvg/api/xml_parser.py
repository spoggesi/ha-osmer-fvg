"""XML Parser for OSMER FVG bulletin XML."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

from ..const import map_osmer_condition
from .models import OsmerForecastDay

_LOGGER = logging.getLogger(__name__)


def _parse_temp_value(val_str: str) -> float | None:
    """Parse temperature value or temperature range string (e.g. '20/23' -> 21.5)."""
    if not val_str or val_str.lower() in ("n.d.", "-"):
        return None
    val_str = val_str.strip()
    if "/" in val_str:
        parts = val_str.split("/")
        try:
            floats = [float(p.strip()) for p in parts if p.strip()]
            if floats:
                return sum(floats) / len(floats)
        except ValueError:
            return None
    try:
        return float(val_str)
    except ValueError:
        return None


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
    """Parse OSMER XML bulletin for the given forecast zone."""

    forecasts: list[OsmerForecastDay] = []
    clean_content = xml_content.strip()

    if not clean_content or clean_content.startswith(("<!DOCTYPE", "<html")):
        _LOGGER.debug("Received invalid XML or HTML response")
        return forecasts

    try:
        root = ET.fromstring(clean_content)
    except ET.ParseError as err:
        _LOGGER.warning("Failed to parse OSMER XML bulletin: %s", err)
        return forecasts

    clean_num = str(target_zone).strip().upper().replace("Z", "").replace("F", "")

    scadenze = root.findall(".//scadenza")
    if not scadenze:
        scadenze = [root]

    for scadenza in scadenze:
        raw_date = (
            scadenza.attrib.get("data_validita")
            or scadenza.attrib.get("data")
            or scadenza.findtext("data")
            or ""
        ).strip()

        if not raw_date:
            continue

        iso_date = _parse_date(raw_date)

        condition_text = ""
        summary_text: str | None = None
        temp_min: float | None = None
        temp_max: float | None = None
        precip_prob: int | None = None

        # Combina le informazioni dei nodi zona (es. Z3 ed F3 condividono il numero "3")
        for z in scadenza.findall(".//zona"):
            z_nome = str(z.attrib.get("nome", "")).strip().upper()
            z_id = str(z.attrib.get("id", "")).strip().upper()
            z_clean = z_nome.replace("Z", "").replace("F", "")

            if (
                z_clean == clean_num
                or z_id == clean_num
                or z_nome == target_zone.upper()
            ):
                # Estrazione condizione e testo sintesi
                cond = (
                    z.findtext("EVOLUZIONE12_DESCRIZIONE")
                    or z.findtext("EVOLUZIONE24_DESCRIZIONE")
                    or z.findtext("EVOLUZIONE00_DESCRIZIONE")
                    or z.findtext("CIELO_DESCRIZIONE")
                    or ""
                )
                if cond and not condition_text:
                    condition_text = cond

                txt = z.findtext("TESTO")
                if txt and not summary_text:
                    summary_text = txt

                # Estrazione temperature (es. TMIN "20/23")
                tmin_txt = z.findtext("TMIN")
                if tmin_txt and temp_min is None:
                    temp_min = _parse_temp_value(tmin_txt)

                tmax_txt = z.findtext("TMAX")
                if tmax_txt and temp_max is None:
                    temp_max = _parse_temp_value(tmax_txt)

                # Estrazione probabilità di precipitazione
                prob_txt = z.findtext("PROBABILITAPRECIPITAZIONI")
                if prob_txt and precip_prob is None:
                    try:
                        precip_prob = int(prob_txt)
                    except ValueError:
                        pass

        if condition_text or temp_min is not None or temp_max is not None:
            forecasts.append(
                OsmerForecastDay(
                    date=iso_date,
                    condition=map_osmer_condition(condition_text),
                    temp_min=temp_min,
                    temp_max=temp_max,
                    precipitation_probability=precip_prob,
                    summary=summary_text,
                )
            )

    return forecasts
