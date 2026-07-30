"""Constants for OSMER FVG integration."""

DOMAIN = "osmer_fvg"


DEFAULT_SCAN_INTERVAL = 15


BASE_URL = (
    "https://monitor.protezionecivile.fvg.it/api"
)


# Default station
DEFAULT_STATION_ID = 209


# Sensors exposed to Home Assistant
#
# key = API sensor code

MONITORED_SENSORS = {

    "T": {
        "name": "Temperatura aria",
        "device_class": "temperature",
        "unit": "°C",
    },

    "U": {
        "name": "Umidità relativa",
        "device_class": "humidity",
        "unit": "%",
    },

    "RR": {
        "name": "Precipitazione",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "P": {
        "name": "Pluviometro",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "IDRO": {
        "name": "Livello idrometrico",
        "device_class": None,
        "unit": "m",
    },

    "Prec_5_min": {
        "name": "Pioggia ultimi 5 minuti",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_60_min": {
        "name": "Pioggia ultima ora",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_24_ore": {
        "name": "Pioggia ultime 24 ore",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_48_ore": {
        "name": "Pioggia ultime 48 ore",
        "device_class": "precipitation",
        "unit": "mm",
    },
}