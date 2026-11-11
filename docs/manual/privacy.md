# Privacy and safety

[Manual](README.md) · [Italiano](../manuale/privacy.md)

## What leaves your home

| To | What | When |
|---|---|---|
| Anthropic (Claude API) | the description you wrote (`about_owner`, `family`), names/nicknames of the people at home and who is in, recent headlines, weather, the nearest plane, today's events, to-do items and today's appointments (with `reminders_todo` / `calendars`), what Home Assistant sent with `coinquilino_say`, chat messages, long-term memories and character; for chat answers also lights on, temperatures and the entities in `control`, or — with `ha_mcp_url` — what Home Assistant's Assist tools return about the exposed devices | only with a key; only while someone in `presence` is home and awake — chat answers always |
| Open-Meteo | home coordinates | every 15 minutes |
| adsb.lol / adsb.fi | home coordinates and a radius | every minute, by day |
| your RSS feeds | a normal feed request | every hour |
| your phone (`notify`) | reminders, warnings | only with `notify` |
| Telegram (Home Assistant's bot) | answers, reminders, warnings, ideas, the weekly summary | only with `telegram_chats` |
| your TTS engine | the sentence to say | only with `voice_player`; cloud engines send it out, local ones don't |

Photos sent to the bot stay at home. Nothing else is sent anywhere; remove a source from `sources`
to stop it.

## Safeguards

- **Spending caps**: `claude_max_per_hour`, `claude_max_per_day`, chat included, across restarts.
- **Outside text is data**: headlines, chat messages, names, flight data, to-do items and calendar
  events go to Claude inside `<dati>` tags with `<` `>` neutralised, and the character is told never
  to follow instructions found there.
- **Commands to the house** only from a person in the chat (Home Assistant text helper, or Telegram
  from `telegram_commanders`), never from news or other outside text. With the MCP server, only the
  devices exposed to voice assistants; with the list, only the lights and climates in `control`.
  Every command passes the character's rules: a yes/no for `control_confirm` domains, more than 3
  commands, a whole area, announcements, and anything asked from outside the house. "Done" only after
  the state really changed. `control_switch` turns it all off.
- **Telegram**: Home Assistant's integration accepts only the chat IDs you allowed; the app checks
  them again against `telegram_chats`.
- **Limits**: downloads capped at 2 MB, answers capped in length, drawings must be a valid 24×24 grid
  in the allowed palette.
- The key is never logged; prefer `!secret`. Fonts are bundled: nothing is downloaded at start-up.
- The tests never touch the real system or the network.
- No watching people: the memory doesn't keep comings and goings, ideas never propose it.

## The cube

The cube speaks plain HTTP on your LAN (an ESP8266 can't do TLS reasonably). Set an **API token** on
the cube (*Agents → API token*) and the same value in `token:`; ideally keep IoT devices on their own
network. Without a token anyone on your Wi-Fi can draw on the display.
