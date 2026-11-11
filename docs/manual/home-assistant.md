# Home Assistant integration

[Manual](README.md) · [Italiano](../manuale/home-assistant.md)

Coinquilino is meant as an extension of Home Assistant: your automations decide what is worth
saying, the character says it well. This page covers what Home Assistant can send to it, what it
reads from Home Assistant, and what it gives back.

## The `coinquilino_say` event

Everything Home Assistant wants the character to say goes through one event. Fire it from an
automation, a script, or *Developer tools → Events*:

```yaml
- event: coinquilino_say
  event_data:
    text: "La lavatrice ha finito."
    away: notify
    night: defer
```

All fields are optional:

| Field | Values | Meaning |
|---|---|---|
| `text` | sentence | said as is (no Claude) |
| `about` | topic | Claude writes it in the character's voice (counts in the caps) |
| `telegram` | true/false | also sent to the phone (Telegram, or `notify`) |
| `away` | `say` · `notify` · `skip` | with nobody home: say it anyway (default), phone only, nothing |
| `night` | `say` · `defer` · `skip` | at night: say it (default), at wake-up, nothing |
| `wait` | true/false | queued with the other warnings (min gap, hourly cap) instead of at once |
| `key` | text | identifies the message: the same key is not repeated… |
| `repeat_hours` | number | …before this many hours (default 12) |
| `remember` | sentence | a fact for today's memory, not said |
| `quiet_seconds` | seconds | no chatter for a while (e.g. the doorbell just rang) |
| `expect_arrival` | true | someone is coming in: the greeting starts at once |
| `mood`, `minutes` | mood name, minutes | a temporary mood (e.g. `welcome`) |
| `cube` (or `instance`) | instance name | only that cube, with more than one |

Notes:

- Messages sent with this event are never blocked by the spontaneous-message cap
  (`message_gap_hours`).
- `away: notify` + nobody home → the phone gets it, the cube doesn't.
- With `night: defer` the message is kept and told in the morning, on the cube and on the phone.
- A message with a `key` that was skipped (night, empty house) does not consume the key.

### The script blueprint

[`blueprints/script/coinquilino/alessio_di.yaml`](../../blueprints/script/coinquilino/alessio_di.yaml)
(*Coinquilino: di' qualcosa*) wraps the event with a form: create a script from it and use it as an
action in the automation editor without writing YAML.

## Blueprints

The rules about the house live in Home Assistant as automation blueprints in
[`blueprints/automation/coinquilino/`](../../blueprints/automation/coinquilino/). Copy the
`blueprints/` folder into Home Assistant's `blueprints/` (or import each file from its GitHub URL in
*Settings → Automations & scenes → Blueprints*), then *Create automation* from each one you want.

| Blueprint | What it does | Inputs |
|---|---|---|
| **Lights left on in an empty house** | after N minutes with `zone.home` at 0, turns off the lights that are on (except those to keep) and says which really went off; phone only with nobody home | zone, minutes (10), turn off (yes), lights to keep |
| **Climate off with an open window** | window open for N minutes and climate on: sets it to off, says so, and puts back the previous mode when the window closes | window, climate, minutes (3) |
| **Doorbell** | on a ring: quiet for a minute and remembers it; if nobody opens within N minutes, says so on the cube and the phone (at night at wake-up); if someone opens, the greeting to who comes in starts at once | ring event entity, open event entity, minutes (2), quiet seconds (60) |
| **Low batteries** | once a day, the battery sensors below the threshold, one line (phone only with nobody home); the same list not again for 3 days | threshold (20%), time (10:00), sensors to ignore |
| **Home Assistant updates** | once a day, the pending `update.*`, to whoever is home; the same list once a week | time (18:00) |
| **Someone on the way home** | with the **Proximity** integration: below N km and heading towards home, Claude says it in its voice to whoever is home; never at night | distance sensor, direction sensor, who, km (5) |
| **Parcels (17TRACK)** | when a 17TRACK counter goes up (delivered, ready to be picked up…), says the sentence you chose; phone only with nobody home | 17TRACK sensor, sentence |

Each blueprint only fires `coinquilino_say`: open it to see exactly what it sends, and copy it as a
starting point for your own rules.

## To-do lists and calendars

| Option | Example | What it does |
|---|---|---|
| `reminders_todo` | `[todo.alessio]` | reads the items to do every 2 minutes |
| `calendars` | `[calendar.family]` | reads today's and tomorrow's appointments every 15 minutes |
| `calendar_minutes` | `60` | how many minutes before an appointment it warns |
| `workday` | `binary_sensor.workday_sensor` | working day or holiday, in what it knows today |

- An item **with a time** is said when due, on the cube and on the phone, once.
- An **appointment** (not all-day) is announced `calendar_minutes` before: "Fra 30 minuti: Dentista
  (alle 16:00)".
- Items without a time and today's appointments go into what the character knows: it can mention
  them, and a free line "Oggi in agenda: …" comes up to 4 times a day.
- In the chat, *"ricordami di chiamare la nonna alle 18"* adds an item with that due time to the
  first list in `reminders_todo` (without a list it keeps the reminder in its own memory);
  *"fatto la nonna"* ticks the matching item off.

Good lists: **Local To-do** (a list just for the character), Alexa's to-do list (fill it from an Echo,
also in the car with Echo Auto), any other `todo.*`. Calendars: **Local Calendar**, Google Calendar,
CalDAV… Workday is the core **Workday** integration.

## Home Assistant's MCP server

With `ha_mcp_url` and `ha_mcp_token` the chat uses the Assist tools of Home Assistant's **Model
Context Protocol Server**: the devices you expose to voice assistants, with their names, areas and
aliases. Home Assistant knows the house; the character adds memory, personality, its confirmation
rules and the log. See [Chat → Commands to the house](chat.md#with-home-assistants-mcp-server-recommended).

## Sensors it publishes

| Entity | State | Attributes |
|---|---|---|
| `sensor.<character>_dice` | the last line | `tipo` (log name), `ora` |
| `sensor.<character>_stato` | the mood | age, holiday, memories, character, interests, reminders, chat-command actions, ideas, photos, last message, version |
| `sensor.<instance>_costo_api` | $ spent this month | `mese`, `oggi`, `chiamate`, `budget` |

They are created by the app (not in the entity registry) and come back within 5 minutes after a
Home Assistant restart. The names change with `sensor`, `state_sensor`, `cost_sensor`.

## Dashboard

[`examples/plancia.yaml`](../../examples/plancia.yaml) is a ready view: chat, switches (voice,
autonomy, commands), mood and age, memories, a logbook of the `coinquilino_*` automations, chat
commands, ideas, the API spending chart, the photo album and, optionally, the live preview.

For the preview set `preview: /homeassistant/www/coinquilino.png` and add a *Local File* camera on
`/config/www/coinquilino.png` (named `camera.anteprima_cubo` in the example).

Useful helpers (create them in *Settings → Devices & services → Helpers*):

| Helper | Option |
|---|---|
| Text, max 255 | `chat_entity` |
| Toggle | `voice_switch`, `autonomy_switch`, `control_switch` |
| Button ×2 | `feedback_up`, `feedback_down` |
| Dropdown + Button ×2 | `photo_select`, `photo_show_button`, `photo_delete_button` |

## More than one cube

Add one instance per cube in `apps.yaml`, each with its own `host` and, if you like, its own
`character`, `chat_entity`, `voice_player`:

```yaml
cucina:
  module: coinquilino
  class: Coinquilino
  host: 192.168.1.51
  character: bandit
  chat_entity: input_text.parla_con_bandit
```

Each instance has its own memory (`memoria_<instance>.json`) and its own sensors. Send
`cube: cucina` in `coinquilino_say` to make only that one talk.
