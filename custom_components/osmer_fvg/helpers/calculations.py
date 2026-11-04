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
        
        # Calculate intermediate values
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
    
    Based on NWS heat index formula, converted from Fahrenheit to Celsius.
    
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
    
    # Convert to Fahrenheit for calculation
    temp_f = (temperature * 9/5) + 32
    
    try:
        # NWS heat index formula
        hi_f = (
            -42.379 
            + 2.04901523 * temp_f 
            + 10.14333127 * humidity 
            - 0.22475541 * temp_f * humidity 
            - 6.83783e-3 * temp_f ** 2 
            - 5.481717e-2 * humidity ** 2 
            + 1.22874e-3 * temp_f ** 2 * humidity 
            + 8.5282e-4 * temp_f * humidity ** 2 
            - 1.99e-6 * temp_f ** 2 * humidity ** 2
        )
        
        # If humidity is very low, use simpler formula
        if humidity < 13 and temp_f >= 80:
            hi_f = (
                -42.379 
                + 2.04901523 * temp_f 
                + 10.14333127 * humidity 
                - 0.22475541 * temp_f * humidity
            )
        
        # Convert back to Celsius
        if hi_f is not None:
            heat_index_c = (hi_f - 32) * 5/9
            return round(heat_index_c, 1)
        return None
    except (ValueError, TypeError):
        return None


def calculate_wind_chill(
    temperature: float | None,
    wind_speed: float | None,
) -> float | None:
    """Calculate wind chill in Celsius.
    
    Wind chill is only calculated when temperature <= 10°C and wind speed >= 4.8 km/h
    Formula: WCI = 13.12 + 0.6215 * T - 11.37 * V^0.16 + 0.3965 * T * V^0.16
    where T is temperature in °C and V is wind speed in km/h
    
    Args:
        temperature: Temperature in Celsius
        wind_speed: Wind speed in m/s (will be converted to km/h)
    
    Returns:
        Wind chill in Celsius or None if conditions are not met or inputs are invalid
    """
    if temperature is None or wind_speed is None:
        return None
    
    # Convert m/s to km/h
    wind_speed_kmh = wind_speed * 3.6
    
    # Wind chill is only calculated for cold conditions
    if temperature > 10.0 or wind_speed_kmh < 4.8:
        return None
    
    try:
        wci = (
            13.12 
            + 0.6215 * temperature 
            - 11.37 * (wind_speed_kmh ** 0.16) 
            + 0.3965 * temperature * (wind_speed_kmh ** 0.16)
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
        # Calculate saturation vapor pressure in hPa
        es = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5))
        
        # Calculate actual vapor pressure in hPa
        ea = es * (relative_humidity / 100.0)
        
        # Calculate absolute humidity in g/m³
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
    
    # Extract base values
    temperature = measures.get("T")
    humidity = measures.get("U")
    wind_speed = measures.get("VV")
    
    temp_value = temperature.value if temperature else None
    humidity_value = humidity.value if humidity else None
    wind_speed_value = wind_speed.value if wind_speed else None
    
    # Calculate derived values
    results["DEW_POINT"] = calculate_dew_point(temp_value, humidity_value)
    results["HEAT_INDEX"] = calculate_heat_index(temp_value, humidity_value)
    results["WIND_CHILL"] = calculate_wind_chill(temp_value, wind_speed_value)
    results["ABS_HUMIDITY"] = calculate_absolute_humidity(temp_value, humidity_value)
    
    return results
