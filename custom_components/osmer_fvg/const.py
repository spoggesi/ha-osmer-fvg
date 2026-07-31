"""Constants for OSMER FVG integration."""

DOMAIN = "osmer_fvg"


DEFAULT_SCAN_INTERVAL = 300


BASE_URL = "https://monitor.protezionecivile.fvg.it/api"


DEFAULT_STATION_ID = 209


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


    # Precipitazioni

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

    "P_1h": {
        "name": "Pioggia oraria",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_5_min": {
        "name": "Precipitazione ultimi 5 minuti",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_60_min": {
        "name": "Precipitazione ultima ora",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_3_ore": {
        "name": "Precipitazione ultime 3 ore",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_6_ore": {
        "name": "Precipitazione ultime 6 ore",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_12_ore": {
        "name": "Precipitazione ultime 12 ore",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_24_ore": {
        "name": "Precipitazione ultime 24 ore",
        "device_class": "precipitation",
        "unit": "mm",
    },

    "Prec_48_ore": {
        "name": "Precipitazione ultime 48 ore",
        "device_class": "precipitation",
        "unit": "mm",
    },


    # Idrologia

    "IDRO": {
        "name": "Livello idrometrico",
        "device_class": None,
        "unit": "m",
    },


    # Alimentazione stazione

    "CAR": {
        "name": "Corrente di carica",
        "device_class": "current",
        "unit": "mA",
    },

    "SCAR": {
        "name": "Corrente di scarica",
        "device_class": "current",
        "unit": "mA",
    },


    # Diagnostica

    "STSpluv (RAW)": {
        "name": "Stato pluviometro",
        "device_class": None,
        "unit": "sts",
    },
}