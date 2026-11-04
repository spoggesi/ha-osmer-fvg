"""Calculations for derived sensors."""

from __future__ import annotations

import math
from typing import Any


def calculate_dew_point(
    temperature: float | None,
    humidity: float | None,
) -> float | None:
    """Calculate dew point in Celsius from temperature and relative humidity.

    Formula: Magnus formula
    Dew Point = (b * ((ln(RH/100) + ((a*T)/(b+T))))) / (a - (ln(RH/100) + ((a*T)/(b+T))))
    where: a = 17.625, b = 243.04

    Args:
        temperature: Temperature in Celsius
        humidity: Relative humidity in percentage (0-100)

    Returns:
        Dew point in Celsius or None if inputs are invalid
    """
    if temperature is None or humidity is None:
        return None

    if humidity <= 0 or humidity > 100:
        return None

    try:
        a = 17.625
        b = 243.04

        ln_rh = math.log(humidity / 100.0)
        numerator = b * (ln_rh + (a * temperature) / (b + temperature))
        denominator = a - (ln_rh + (a * temperature) / (b + temperature))

        dew_point = numerator / denominator
        return round(dew_point, 1)
    except (ValueError, ZeroDivisionError):
        return None


def calculate_heat_index(
    temperature: float | None,
    humidity: float | None,
) -> float | None:
    """Calculate heat index (feels like temperature) in Celsius.

    Based on NWS algorithm. Heat Index is only applicable for warm temperatures (>= 26.7°C / 80°F).
    Below 26.7°C, relative humidity does not cause heat stress, so ambient temperature is returned.

    Args:
        temperature: Temperature in Celsius
        humidity: Relative humidity in percentage (0-100)

    Returns:
        Heat index in Celsius or None if inputs are invalid
    """
    if temperature is None or humidity is None:
        return None

    if humidity < 0 or humidity > 100:
        return None

    # L'indice di calore ha senso solo a partire da 26.7°C (80°F).
    # Al di sotto di questa soglia, la temperatura percepita è la temperatura reale.
    if temperature < 26.7:
        return round(temperature, 1)

    # Conversione in Fahrenheit per le equazioni NWS
    temp_f = (temperature * 9 / 5) + 32

    try:
        # Equazione semplice di Steadman
        hi_simple = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (humidity * 0.094))

        if hi_simple < 80.0:
            hi_f = hi_simple
        else:
            # Regressione completa Rothfusz (NWS)
            hi_f = (
                -42.379
                + 2.04901523 * temp_f
                + 10.14333127 * humidity
                - 0.22475541 * temp_f * humidity
                - 6.83783e-3 * (temp_f**2)
                - 5.481717e-2 * (humidity**2)
                + 1.22874e-3 * (temp_f**2) * humidity
                + 8.5282e-4 * temp_f * (humidity**2)
                - 1.99e-6 * (temp_f**2) * (humidity**2)
            )

            # Correzione NWS per aria molto secca
            if humidity < 13 and 80.0 <= temp_f <= 112.0:
                adjustment = ((13.0 - humidity) / 4.0) * math.sqrt(
                    (17.0 - abs(temp_f - 95.0)) / 17.0
                )
                hi_f -= adjustment
            # Correzione NWS per aria molto umida
            elif humidity > 85 and 80.0 <= temp_f <= 87.0:
                adjustment = ((humidity - 85.0) / 10.0) * ((87.0 - temp_f) / 5.0)
                hi_f += adjustment

        heat_index_c = (hi_f - 32) * 5 / 9
        # L'umidità non può abbassare la temperatura percepita estiva al di sotto di quella reale
        return round(max(heat_index_c, temperature), 1)
    except (ValueError, TypeError):
        return round(temperature, 1)


def calculate_wind_chill(
    temperature: float | None,
    wind_speed: float | None,
) -> float | None:
    """Calculate wind chill in Celsius.

    Wind chill is only calculated when temperature <= 10°C and wind speed >= 4.8 km/h.
    Formula: WCI = 13.12 + 0.6215 * T - 11.37 * V^0.16 + 0.3965 * T * V^0.16
    where T is temperature in °C and V is wind speed in km/h.

    Args:
        temperature: Temperature in Celsius
        wind_speed: Wind speed in m/s (will be converted to km/h)

    Returns:
        Wind chill in Celsius or None if conditions are not met or inputs are invalid
    """
    if temperature is None or wind_speed is None:
        return None

    # Conversione m/s in km/h
    wind_speed_kmh = wind_speed * 3.6

    # Il Wind Chill si calcola solo in condizioni di freddo e vento attivo
    if temperature > 10.0 or wind_speed_kmh < 4.8:
        return None

    try:
        wci = (
            13.12
            + 0.6215 * temperature
            - 11.37 * (wind_speed_kmh**0.16)
            + 0.3965 * temperature * (wind_speed_kmh**0.16)
        )
        return round(wci, 1)
    except (ValueError, TypeError):
        return None


def calculate_absolute_humidity(
    temperature: float | None,
    relative_humidity: float | None,
) -> float | None:
    """Calculate absolute humidity in g/m³.

    Formula: AH = (6.112 * e^(17.67*T/(T+243.5)) * RH * 2.16679) / (273.15 + T)

    Args:
        temperature: Temperature in Celsius
        relative_humidity: Relative humidity in percentage (0-100)

    Returns:
        Absolute humidity in g/m³ or None if inputs are invalid
    """
    if temperature is None or relative_humidity is None:
        return None

    if relative_humidity <= 0 or relative_humidity > 100:
        return None

    try:
        # Pressione di vapore saturo in hPa
        es = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5))

        # Pressione di vapore reale in hPa
        ea = es * (relative_humidity / 100.0)

        # Umidità assoluta in g/m³
        absolute_humidity = (ea * 2.16679) / (273.15 + temperature)

        return round(absolute_humidity, 1)
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def calculate_derived_sensors(
    measures: dict[str, Any],
) -> dict[str, float | None]:
    """Calculate all derived sensor values from measures.

    Args:
        measures: Dictionary of sensor code -> Measure object with value attribute

    Returns:
        Dictionary of derived sensor code -> calculated value
    """
    results: dict[str, float | None] = {}

    temperature = measures.get("T")
    humidity = measures.get("U")
    wind_speed = measures.get("VV")

    temp_value = temperature.value if temperature else None
    humidity_value = humidity.value if humidity else None
    wind_speed_value = wind_speed.value if wind_speed else None

    results["DEW_POINT"] = calculate_dew_point(temp_value, humidity_value)
    results["HEAT_INDEX"] = calculate_heat_index(temp_value, humidity_value)
    results["WIND_CHILL"] = calculate_wind_chill(temp_value, wind_speed_value)
    results["ABS_HUMIDITY"] = calculate_absolute_humidity(temp_value, humidity_value)

    return results