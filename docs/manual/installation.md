# Installation

[Manual](README.md) · [Italiano](../manuale/installazione.md)

## What you need

- A **GeekMagic SmallTV Ultra** (ESP8266, 240×240 display).
- **Home Assistant** with the **AppDaemon** add-on (tested with AppDaemon 4.5).
- Optional: an **Anthropic API key** (lines written by Claude), a **TTS** integration and a speaker,
  the **Telegram bot** integration, the integrations used by the blueprints (Proximity, 17TRACK…).

## 1. The firmware

The cube runs [glimmer](https://github.com/Avinava/glimmer), an open firmware, plus the patch in
[`firmware/`](../../firmware/) that adds a **Pixel** channel: the cube stores nothing and streams the
frames it receives straight to the panel. Build, flash and first set-up are described in
[`firmware/README.md`](../../firmware/README.md).

On the cube's web page:

- set an **API token** (*Agents → API token*) and write the same value in `token:` in the personal
  file — without it anyone on your Wi-Fi can draw on the display;
- turn off the channels you don't want; the Pixel channel is on by default.

## 2. AppDaemon

In the add-on configuration add `pillow` to `python_packages` and restart the add-on.

## 3. The app

Copy the folder `apps/coinquilino/` (Python files and `fonts/`) into AppDaemon's `apps` folder. With
the add-on that is `/addon_configs/a0d7b954_appdaemon/apps/` (on recent versions
`/app_configs/a0d7b954_appdaemon/apps/`). With HACS you can add this repository as a custom
repository of type *AppDaemon*.

Add the instance to `apps/apps.yaml` (see [`examples/apps.yaml`](../../examples/apps.yaml)):

```yaml
coinquilino:
  module: coinquilino
  class: Coinquilino
```

## 4. The personal file

Copy [`examples/coinquilino_personale.yaml`](../../examples/coinquilino_personale.yaml) as
`coinquilino_personale.yaml` **next to `appdaemon.yaml`**, one level above `apps/` — not inside it:
AppDaemon reads every YAML file under `apps/` as app configuration.

Only `host` is required. A good first file:

```yaml
host: 192.168.1.50
token: "0123"
owner: Zio Mario
owner_entity: person.mario
presence: [person.mario]
city: Bologna
anthropic_api_key: !secret anthropic_api_key
```

`!secret` reads AppDaemon's or Home Assistant's `secrets.yaml`; `!env_var` works too. When you save
the file the app notices and restarts within 20 seconds.

## 5. First start

AppDaemon loads the app by itself. In the add-on log look for:

```
coinquilino 3.0.5 pronto (alessio): cubo 192.168.1.50, persone [...], battute da Claude SI (...)
```

and for warnings right after it (an unreachable cube, a missing token). See
[Log and troubleshooting](troubleshooting.md).

## 6. Optional pieces

| What | How | Manual |
|---|---|---|
| Chat from a dashboard | a *Text* helper (max 255) → `chat_entity` | [Chat](chat.md) |
| Telegram | Telegram bot integration (Polling) → `telegram_chats` | [Chat](chat.md#telegram) |
| Voice | a `tts.*` entity and a media player → `voice_player`, `voice_tts` | [Chat](chat.md#voice) |
| Commands to the house | the *Model Context Protocol Server* integration → `ha_mcp_url`, `ha_mcp_token` (or a `control:` list) | [Chat](chat.md#commands-to-the-house) |
| Blueprints | copy `blueprints/` into Home Assistant | [Home Assistant](home-assistant.md#blueprints) |
| Agenda | `reminders_todo`, `calendars`, `workday` | [Home Assistant](home-assistant.md#to-do-lists-and-calendars) |
| Dashboard | paste `examples/plancia.yaml` | [Home Assistant](home-assistant.md#dashboard) |
| Photos | Telegram + `/media` | [On the cube](on-the-cube.md#family-photos) |

## Updating

Copy the new Python files over the old ones: AppDaemon restarts the app on its own and the memory is
kept (`apps/memoria.json`). The [CHANGELOG](../../CHANGELOG.md) says what changed.
