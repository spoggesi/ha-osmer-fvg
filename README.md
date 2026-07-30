# OSMER FVG - Home Assistant Integration

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue)
![Version](https://img.shields.io/github/v/release/spoggesi/ha-osmer-fvg)

Integrazione custom per Home Assistant che permette di monitorare le stazioni meteorologiche **OSMER FVG** (Osservatorio Meteorologico Regionale del Friuli Venezia Giulia).

---

## Funzionalità

Attualmente supporta:

- 🌡 Temperatura aria
- 💧 Umidità relativa
- 🌧 Precipitazioni
- 🌊 Livello idrometrico
- 📍 Informazioni stazione
- 🔄 Aggiornamento automatico tramite API OSMER

---

## Installazione tramite HACS

### Aggiunta repository personalizzato

1. Aprire Home Assistant
2. Andare in: HACS → integrazioni
3. Menu in alto a destra: 
4. Inserire: https://github.com/spoggesi/ha-osmer-fvg 
5. Installare **OSMER FVG**
6. Riavviare Home Assistant

## Configurazione

Dopo il riavvio:
Impostazioni
→ Dispositivi e servizi
→ Aggiungi integrazione
→ OSMER FVG

Selezionare la stazione meteorologica desiderata.

---

## Sensori disponibili

Esempio:
OSMER Zuiano
Temperatura aria
Umidità
Pioggia
Precipitazione
Livello idrometrico

---

## API

I dati vengono forniti dal servizio pubblico:

OSMER FVG / Protezione Civile Friuli Venezia Giulia
https://monitor.protezionecivile.fvg.it

---

## Supporto

Per segnalazioni o richieste:

https://github.com/spoggesi/ha-osmer-fvg/issues

---

## Licenza

MIT License