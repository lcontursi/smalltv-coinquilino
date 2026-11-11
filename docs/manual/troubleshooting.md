# Log and troubleshooting

[Manual](README.md) · [Italiano](../manuale/problemi.md)

## Reading the log

The AppDaemon add-on log has one line per thing that happened:

```
SAY    free chatter weather.now       : Fuori ci sono 14 gradi e c'è il sole.
QUEUE  free event   person.leave      : Anna (person.anna)
QUEUE  paid timer   director
CLAUDE paid timer   director          : 1834+62 token | oggi 12/150, ultima ora 3/20 | 0.0004 $
SAY    paid timer   director          : Zio Mario, la biblioteca nuova apre sabato.
SAY    free (fallback) event person.arrive : Ciao Anna, eccoti a casa.
SKIP   free event   say               : luci_casa_vuota: già detto
ACT    free chat    home.agenda       : todo.alessio: chiamare la nonna
```

- `SAY` said · `QUEUE` waiting its turn · `SKIP` dropped, with the reason · `CLAUDE` an API call,
  with real tokens, caps and cost · `ACT` an action done on Home Assistant.
- `free` / `paid`: paid only when Claude wrote the line; `free (fallback)` means Claude was meant to
  but a built-in line was used (no key, nobody home, cap reached, error — the reason is logged).
- Groups: `chatter` (free lines), `event` (something happened), `timer` (director, drawing, diary,
  night work), `chat`.

### Names in the log

These are also the names for `chatter_day_max` and `voice_kinds`:

| Free chatter | | Events and timers | |
|---|---|---|---|
| `weather.now` | current weather | `person.arrive` / `person.leave` | arrivals, departures |
| `weather.forecast` | forecast | `weather.rain_soon` / `rain_stop` / `wind` / `change` / `morning` | weather warnings |
| `weather.chart` | week on the blackboard | `plane.overhead` | plane above the house |
| `home.status` / `home.people` | home, who is in | `holiday` | holidays, birthdays |
| `home.agenda` | today's agenda | `say` | `coinquilino_say` |
| `news.headline` | a headline | `director` / `drawing` / `diary` | Claude timers |
| `sky.sun` / `calendar.today` | sun, the day | `chat.reply` | chat answers |
| `planes.nearby` / `planes.radar` | planes | `me.reminder` | reminders |
| `me.fact` / `me.gallery` | curiosity, drawings | `home.temperature` | a room changing fast |
| | | `home.read` / `home.confirm` / `home.action` | commands to the house: reads, yes/no, actions |
| `claude.usage` / `claude.chart` / `api.usage` | Claude | `memory.night` / `character.week` / `me.idea` | night work |
| `screen.weather` / `screen.home` / `screen.power` | screens | `claude.low` / `claude.refilled` | Claude session |
| `me.showcase` | today's showcase | `api.budget` | spending warning |

## Common problems

**The cube shows only the face for a long time.** At night that's normal. By day the first line
after a restart comes within a minute and a half; then with only the face on screen it tries every
minute. If nothing arrives, look for `chiacchiere in pausa` in the log (debug level) — empty house,
the doorbell (`quiet_seconds`), items in the queue.

**`cubo non raggiungibile`.** The cube's Wi-Fi is weak: occasional time-outs are normal and it
recovers. If it lasts, check the IP and that the cube is on the Pixel channel firmware.

**`il cubo rifiuta il token`.** `token:` doesn't match the cube's API token (quote it if it starts with 0).

**`Entity … not found in the default namespace`.** AppDaemon's own check: the entity is not in its
copy of the states yet (for example a list just created). The call goes through anyway; if it
repeats, check the entity name.

**"Entity not found" on the dashboard after a restart of Home Assistant.** The app's sensors come
back within 5 minutes.

**Commands don't work (MCP server).** Check in this order:

- `server MCP di Home Assistant non raggiungibile` — the address in `ha_mcp_url` (from the add-on,
  `http://<Home Assistant IP>:8123/api/mcp` always works) or the token: it must be a long-lived
  access token of a user with access;
- Claude answers about the house but never acts — the integration's *Read-only* option is on, or
  *Device control* is not selected;
- `nome sconosciuto ad Assist` — the device is not exposed to voice assistants, or it has another
  name: expose it, or give it an alias, in *Settings → Voice assistants → Expose*;
- `SKIP … home.action … lo stato non è cambiato` — Home Assistant accepted the command but the device
  did not change (offline, slow): the character says it couldn't.

**Claude never writes.** Look at the start-up line (`battute da Claude SI/NO`), then for
`free (fallback)` and its reason: nobody of `presence` home, night, cap reached, key wrong.

**It repeats something.** Topics already said today are listed in what Claude receives and the
same free sentence doesn't come back within 3 hours; for Home Assistant messages use `key` and
`repeat_hours`. Tell it in the chat *"non parlare più di …"* to block a topic.

**The personal file changed but nothing happened.** The app checks it every 20 seconds; the log
says `coinquilino_personale.yaml e' cambiato: riparto`. A YAML error is logged at start-up.

## Development

```sh
pip install pillow requests pyyaml pytest ruff
ruff check apps tests
pytest -q
```

The tests run without AppDaemon and without network, with a fake Home Assistant and a fake cube
(`tests/conftest.py`); they also load every blueprint and check the fields it sends.
