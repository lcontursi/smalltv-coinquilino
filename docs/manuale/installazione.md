# Installazione

[Manuale](README.md) · [English](../manual/installation.md)

## Cosa serve

- Un **GeekMagic SmallTV Ultra** (ESP8266, schermo 240×240).
- **Home Assistant** con l'add-on **AppDaemon** (provato con AppDaemon 4.5).
- Facoltativi: una **chiave API di Anthropic** (le frasi le scrive Claude), un'integrazione **TTS**
  e un altoparlante, l'integrazione **Telegram bot**, le integrazioni usate dai blueprint
  (Proximity, 17TRACK…).

## 1. Il firmware

Il cubo usa [glimmer](https://github.com/Avinava/glimmer), un firmware aperto, più la patch in
[`firmware/`](../../firmware/) che aggiunge il canale **Pixel**: il cubo non salva niente e manda allo
schermo i fotogrammi che riceve. Compilazione, caricamento e prima configurazione sono in
[`firmware/README.md`](../../firmware/README.md).

Nella pagina web del cubo:

- imposta un **token API** (*Agents → API token*) e scrivi lo stesso valore in `token:` nel file
  personale — senza, chiunque sia sul tuo Wi-Fi può disegnare sullo schermo;
- spegni i canali che non ti servono; il canale Pixel è acceso di serie.

## 2. AppDaemon

Nella configurazione dell'add-on aggiungi `pillow` a `python_packages` e riavvia l'add-on.

## 3. L'app

Copia la cartella `apps/coinquilino/` (i file Python e `fonts/`) nella cartella `apps` di AppDaemon.
Con l'add-on è `/addon_configs/a0d7b954_appdaemon/apps/` (nelle versioni recenti
`/app_configs/a0d7b954_appdaemon/apps/`). Con HACS puoi aggiungere questo repository come
repository personalizzato di tipo *AppDaemon*.

Aggiungi l'istanza in `apps/apps.yaml` (vedi [`examples/apps.yaml`](../../examples/apps.yaml)):

```yaml
coinquilino:
  module: coinquilino
  class: Coinquilino
```

## 4. Il file personale

Copia [`examples/coinquilino_personale.yaml`](../../examples/coinquilino_personale.yaml) come
`coinquilino_personale.yaml` **accanto ad `appdaemon.yaml`**, un livello sopra `apps/` — non dentro:
AppDaemon legge ogni file YAML in `apps/` come configurazione di un'app.

Serve solo `host`. Un buon primo file:

```yaml
host: 192.168.1.50
token: "0123"
owner: Zio Mario
owner_entity: person.mario
presence: [person.mario]
city: Bologna
anthropic_api_key: !secret anthropic_api_key
```

`!secret` legge il `secrets.yaml` di AppDaemon o di Home Assistant; funziona anche `!env_var`.
Quando salvi il file l'app se ne accorge e riparte entro 20 secondi.

## 5. Il primo avvio

AppDaemon carica l'app da solo. Nel log dell'add-on cerca:

```
coinquilino 3.0.5 pronto (alessio): cubo 192.168.1.50, persone [...], battute da Claude SI (...)
```

e gli avvisi subito dopo (cubo non raggiungibile, token mancante). Vedi
[Log e problemi](problemi.md).

## 6. I pezzi facoltativi

| Cosa | Come | Manuale |
|---|---|---|
| Chat da una plancia | un aiutante *Testo* (max 255) → `chat_entity` | [Chat](chat.md) |
| Telegram | integrazione Telegram bot (Polling) → `telegram_chats` | [Chat](chat.md#telegram) |
| Voce | un'entità `tts.*` e un media player → `voice_player`, `voice_tts` | [Chat](chat.md#la-voce) |
| Comandi alla casa | l'integrazione *Model Context Protocol Server* → `ha_mcp_url`, `ha_mcp_token` (o un elenco `control:`) | [Chat](chat.md#comandi-alla-casa) |
| Blueprint | copia `blueprints/` in Home Assistant | [Home Assistant](home-assistant.md#i-blueprint) |
| Agenda | `reminders_todo`, `calendars`, `workday` | [Home Assistant](home-assistant.md#liste-e-calendari) |
| Plancia | incolla `examples/plancia.yaml` | [Home Assistant](home-assistant.md#la-plancia) |
| Foto | Telegram + `/media` | [Sul cubo](sul-cubo.md#le-foto-di-famiglia) |

## Aggiornare

Copia i nuovi file Python sopra i vecchi: AppDaemon riavvia l'app da solo e la memoria resta
(`apps/memoria.json`). Il [CHANGELOG](../../CHANGELOG.md) dice cosa è cambiato.
