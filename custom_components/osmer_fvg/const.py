"""Constants for OSMER FVG integration."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)

DOMAIN = "osmer_fvg"

DEFAULT_SCAN_INTERVAL = 300

BASE_URL = "https://monitor.protezionecivile.fvg.it/api"

DEFAULT_STATION_ID = 209

MONITORED_SENSORS = {
    "T": {
        "name": "Temperatura aria",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "°C",
        "icon": "mdi:thermometer",
    },
    "U": {
        "name": "Umidità relativa",
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "%",
        "icon": "mdi:water-percent",
    },
    # Precipitazioni (TOTAL_INCREASING per statistiche ed Energy/Weather dashboard)
    "RR": {
        "name": "Precipitazione",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    "P": {
        "name": "Pluviometro",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    "P_1h": {
        "name": "Pioggia oraria",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    "Prec_5_min": {
        "name": "Precipitazione ultimi 5 minuti",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    "Prec_60_min": {
        "name": "Precipitazione ultima ora",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    "Prec_3_ore": {
        "name": "Precipitazione ultime 3 ore",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    "Prec_6_ore": {
        "name": "Precipitazione ultime 6 ore",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    "Prec_12_ore": {
        "name": "Precipitazione ultime 12 ore",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    "Prec_24_ore": {
        "name": "Precipitazione ultime 24 ore",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    "Prec_48_ore": {
        "name": "Precipitazione ultime 48 ore",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "mm",
        "icon": "mdi:weather-rainy",
    },
    # Idrologia
    "IDRO": {
        "name": "Livello idrometrico",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "m",
        "icon": "mdi:waves",
    },
    # Alimentazione stazione
    "CAR": {
        "name": "Corrente di carica",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "mA",
        "icon": "mdi:battery-charging",
    },
    "SCAR": {
        "name": "Corrente di scarica",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "mA",
        "icon": "mdi:battery-minus",
    },
    # Diagnostica
    "STSpluv (RAW)": {
        "name": "Stato pluviometro",
        "device_class": None,
        "state_class": None,
        "unit": "sts",
        "icon": "mdi:information-outline",
    },
}
