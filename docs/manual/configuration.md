# Configuration

[Manual](README.md) · [Italiano](../manuale/configurazione.md)

## Where settings come from

Later ones win:

1. built-in defaults;
2. the **personal file** `coinquilino_personale.yaml`, next to `appdaemon.yaml` — names, entities,
   keys: everything about you. It is in `.gitignore` and never published;
3. the **instance** in `apps/apps.yaml` — only what differs from one cube to another.

The commented file [`examples/coinquilino_personale.yaml`](../../examples/coinquilino_personale.yaml)
lists every option with its default. Saving the personal file restarts the app within 20 seconds.

The names used for chatter kinds (`chatter_day_max`, `voice_kinds`) are the ones in the log — see
[Log and troubleshooting](troubleshooting.md#names-in-the-log).

## The cube

| Option | Default | Meaning |
|---|---|---|
| `host` | — | IP of the cube (required) |
| `token` | none | glimmer API token; quote it if it starts with 0 |
| `character` | `alessio` | `alessio` or `bandit` |
| `gamma` | 1.6 | >1 darkens mid-tones (the panel is bright) |
| `saturation` | 1.4 | >1 stronger colours |
| `night_dim` | 0.25 | brightness of the image at night (with `night_clock: off`) |
| `night_clock` | `alessio` | at night: `alessio` (its clock), `glimmer` (glimmer's), `off` (dimmed room) |
| `wait_text` | — | text glimmer shows while waiting for frames |
| `filler_show` | true | free lines bring the cube back to the Pixel channel |

## People and the house

| Option | Default | Meaning |
|---|---|---|
| `owner` | — | how the character calls the main person ("Zio Mario") |
| `owner_entity` | — | that person's `person.*` |
| `presence` | all persons | Claude is used only if at least one of them is home |
| `nicknames` | friendly names | `person.* → name` used in lines |
| `city` | — | used in lines and in the weather |
| `about_owner`, `family` | — | a few sentences about you and the family, for Claude |
| `persona` | built-in | replaces the character description (advanced) |
| `birthdays` | — | `"MM-DD": name`, the character's own included |
| `away_minutes` | 15 | shorter trips are GPS bounces, not departures |
| `arrive_group_seconds` | 90 | people arriving together get one greeting |
| `indoor_temperature` | average of `climate.*` | sensors to average for "inside it's N degrees" |
| `power_sensor`, `energy_sensor` | none | W now, kWh since midnight, for the power screen |
| `room_change_degrees` | 1.5 | a room changing this much in an hour is worth saying |

## What it talks about

| Option | Default | Meaning |
|---|---|---|
| `sources` | `[casa, meteo, notizie, curiosita, aerei]` | remove one to stop it |
| `feeds` | — | RSS feeds: `url`, `label`, `skip` (categories or whole words) |
| `local_feast` | — | your patron saint: `{from: "MM-DD", to: "MM-DD", name: ...}` |
| `feste` | true | costumes and decorations |
| `weather` | first `weather.*` | entity for the current weather |
| `latitude`, `longitude` | `zone.home` | for Open-Meteo and planes |
| `morning_at` | `"07:45"` | morning greeting with the forecast |
| `diary_at` | `"21:00"` | from this time it writes the day's diary |
| `plane_radius_km` | 15 | planes considered for radar and chatter |
| `overhead_km` | 3 | "above the house": announced and seen through the window |
| `plane_min_altitude_m` | 150 | lower ones are on the ground |
| `plane_gap_minutes` | 10 | at most one announcement every 10 minutes |
| `plane_topic_minutes` | 60 | at most one talk about planes per hour, in all |

## How much it talks

| Option | Default | Meaning |
|---|---|---|
| `talk_every_minutes` | 5 | free chatter (1 minute when the cube shows only the face) |
| `chatter_minutes` | 25 | the director's interval |
| `min_gap_minutes` | 15 | between two queued warnings (urgent ones always pass) |
| `max_per_hour` | 4 | queued warnings per hour |
| `chatter_day_max` | built-in | daily cap per chatter kind, e.g. `{news.headline: 8}` |
| `show_minutes` | 20 | how long a line (short or long), a blackboard or a screen stays |
| `card_seconds` | 40 | minimum time for blackboards and screens |
| `cards` | true | charts, radar and drawings on the blackboard |
| `screens` | true | full-cube screens |
| `scenes` | true | the room changes every day |
| `drawing_hours` | 3 | at most one drawing every 3 hours |
| `night_start`, `night_end` | 23, 7 | asleep from… to… |
| `message_gap_hours` | 3 | one spontaneous phone message every N hours, never at night |
| `spontaneous` | true | an idea or a question a day, the Sunday summary |
| `ideas_avoid` | — | topics it must not propose ideas about |

## Claude

| Option | Default | Meaning |
|---|---|---|
| `anthropic_api_key` | none | without it, built-in lines |
| `model` | `claude-haiku-5-5` | the model |
| `claude_max_per_hour` / `claude_max_per_day` | 20 / 150 | hard caps, chat included |
| `claude_thinking` | false | let the model reason on short lines (costs more) |
| `batch` | true | night work through the Batch API, half price |
| `night_job_at` | `"03:30"` | memories every night, character on Sundays |
| `api_price_in` / `api_price_out` | 0.10 / 0.50 | $ per million tokens, for the spending sensor |
| `api_budget_month` | none | $ per month: warning at 80% |
| `tired_at` | 80 | "tired" above this % of the Claude session (usage sensors) |

## The character

| Option | Default | Meaning |
|---|---|---|
| `age` | 10 | Alessio's age (from 8 he looks like a boy) |
| `grow` | false | true: grows from `start_age` one year every `grow_days` up to `max_age` |
| `force_mood`, `force_festa` | — | for tests: a fixed mood or holiday |
| `moto_days`, `moto_min`, `moto_max` | `[5, 6]`, 15, 30 | "a day for the bike": days and temperatures |
| `feedback_up`, `feedback_down` | — | `input_button` 👍/👎 on the last line |

## Home Assistant

| Option | Default | Meaning |
|---|---|---|
| `ha_mcp_url`, `ha_mcp_token` | — | Home Assistant's MCP server and a long-lived token: commands from the chat ([details](chat.md#with-home-assistants-mcp-server-recommended)) |
| `reminders_todo` | — | to-do lists to read (and where chat reminders go) |
| `calendars` | — | calendars for today's and tomorrow's appointments |
| `calendar_minutes` | 60 | how early it warns about an appointment |
| `workday` | — | Workday `binary_sensor`: working day or holiday |
| `notify` | — | `notify.*` service for phone messages (Telegram first, if set) |
| `autonomy`, `autonomy_switch` | false | the director may send a phone warning |
| `sensor` | `sensor.<name>_dice` | last line |
| `state_sensor` | `sensor.<name>_stato` | mood, memories, ideas… for the dashboard |
| `cost_sensor` | `sensor.<instance>_costo_api` | API spending this month |
| `preview` | none | PNG path for a live preview of the cube |

## Chat, Telegram, voice, commands, photos

These are described with examples in [Chat, Telegram and voice](chat.md) and
[On the cube](on-the-cube.md#family-photos): `chat_entity`, `chat_from`, `chat_reply_phone`,
`telegram_chats`, `telegram_commanders`, `telegram_notify`, `telegram_aloud`, `telegram_event`,
`telegram_bot`, `control`, `control_confirm`, `control_switch`, `control_verify_seconds`,
`voice_player`, `voice_tts`, `voice_language`, `voice_options`, `voice_volume`, `voice_kinds`,
`voice_switch`, `photos`, `photo_every_minutes`, `photo_seconds`, `photo_day_max`, `photo_max`,
`photo_inbox`, `photo_dir`, `photo_saturation`, `photo_select`, `photo_show_button`,
`photo_delete_button`.
