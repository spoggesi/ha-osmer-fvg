# OSMER FVG - Home Assistant Integration

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue)
![HACS](https://img.shields.io/badge/HACS-Custom-orange)
![Version](https://img.shields.io/github/v/release/spoggesi/ha-osmer-fvg)
![License](https://img.shields.io/github/license/spoggesi/ha-osmer-fvg)

<p align="center">
  <img src="logo.png" width="300">
</p>

## Descrizione

**OSMER FVG** è un'integrazione custom per **Home Assistant** che permette di monitorare le stazioni meteorologiche dell'

**OSMER - Osservatorio Meteorologico Regionale del Friuli Venezia Giulia**

integrando i dati pubblici forniti dalla **Protezione Civile Friuli Venezia Giulia**.

L'integrazione non richiede account, API key o configurazioni esterne.

---

# Funzionalità

## Selezione della stazione

L'integrazione permette di configurare una stazione meteorologica tramite:

- 📡 Selezione diretta dall'elenco delle stazioni disponibili
- 📍 Ricerca tramite indirizzo
- 📏 Individuazione automatica delle stazioni più vicine

Durante la configurazione vengono mostrati:

- nome della stazione
- distanza dall'indirizzo selezionato
- sensori disponibili

---

## Sensori supportati

I sensori vengono creati automaticamente in base alle informazioni fornite dalla stazione OSMER selezionata.

Sensori attualmente supportati:

- 🌡️ Temperatura aria
- 💧 Umidità relativa
- 🌧️ Precipitazioni
- 🌊 Livello idrometrico
- 📊 Altri parametri disponibili dalle API OSMER

Durante la configurazione è possibile scegliere quali sensori creare.

---

# Installazione

## Installazione tramite HACS (consigliata)

1. Aprire **Home Assistant**
2. Andare su **HACS → Integrazioni**
3. Cercare **OSMER FVG**
4. Installare l'integrazione
5. Riavviare Home Assistant

---

## Installazione manuale

1. Scaricare il repository:

https://github.com/spoggesi/ha-osmer-fvg

2. Copiare la cartella `custom_components/osmer_fvg` nella directory `config/custom_components/`.

3. Riavviare Home Assistant.

---

# Configurazione

Dopo il riavvio:

**Impostazioni → Dispositivi e servizi → Aggiungi integrazione → OSMER FVG**

La configurazione guidata permette di scegliere il metodo preferito.

---

# Selezione stazione

## Selezione diretta

È possibile scegliere direttamente una stazione dall'elenco disponibile.

Esempio:

- 🌡️ 💧 🌧️ Pordenone
- 🌡️ 💧 Udine
- 🌧️ Tarvisio

Le icone indicano i sensori disponibili nella stazione.

---

## Ricerca tramite indirizzo

Inserendo un indirizzo come:

`Via Roma 1, Pordenone`

l'integrazione calcola automaticamente le stazioni meteorologiche più vicine.

Vengono mostrati:

- nome della stazione
- distanza stimata
- sensori disponibili

---

# Sensori creati

Ogni stazione configurata crea un dispositivo Home Assistant contenente i sensori disponibili.

Esempio:

## OSMER Pordenone

| Sensore | Descrizione |
|---|---|
| Temperatura | Temperatura dell'aria |
| Umidità | Umidità relativa |
| Pioggia | Precipitazione |
| Precipitazione 24h | Accumulo ultime 24 ore |
| Livello idrometrico | Altezza livello acqua |

---

# Aggiornamento dati

I dati vengono aggiornati automaticamente tramite polling delle API pubbliche OSMER.

Non sono necessari:

- ❌ Account utente
- ❌ API key
- ❌ Configurazioni lato server

È sufficiente una connessione internet attiva.

---

# Origine dati

I dati provengono dal servizio pubblico:

**OSMER FVG - Protezione Civile Friuli Venezia Giulia**

https://monitor.protezionecivile.fvg.it

---

# Diagnostica

L'integrazione supporta la diagnostica nativa di Home Assistant.

Sono disponibili informazioni su:

- stazione configurata
- coordinate
- sensori disponibili
- ultimo aggiornamento dati
- stato comunicazione API

---

# Requisiti

- Home Assistant >= 2024.1.0
- Connessione internet attiva
- Accesso alle API pubbliche OSMER FVG

---

# Screenshot

Gli screenshot dell'integrazione saranno aggiunti nelle prossime versioni.

---

# Supporto

Per segnalazioni, richieste o suggerimenti:

https://github.com/spoggesi/ha-osmer-fvg/issues

---

# Contributi

Sono benvenuti:

- segnalazioni di problemi
- nuove funzionalità
- miglioramenti del codice
- supporto per nuovi sensori

---

# Licenza

Questo progetto è rilasciato sotto licenza **MIT**.