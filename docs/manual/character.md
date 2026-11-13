# The character

[Manual](README.md) · [Italiano](../manuale/personaggio.md)

## Alessio

A sharp, slightly ironic 10-year-old (`age`) who calls the owner "Zio". Every line has to carry
something concrete — a number, a time, a difference from yesterday, something to do — and no baby
talk. From 8 years up he has hair, eyebrows and a T-shirt; with `grow: true` he grows up over time
(from `start_age`, one year every `grow_days`, up to `max_age`).

`about_owner`, `family` and `nicknames` tell Claude who lives in the house; `persona` replaces the
whole description if you want a different character.

## The director

Every `chatter_minutes` (25), if someone in `presence` is home and awake and the cube is free, Claude
receives what the character knows — home, weather compared with the past days, news, planes,
agenda, today's events, memories, topics already said today — and writes the one line most worth
saying, with a mood. It can also mark a news item as told, and, with `autonomy`, add a short warning
for the phone (at most one every 3 hours).

Since 3.1 each turn has a **topic**, drawn with a weight among those that still have room today:

| Topic | Weight | Per day | What Claude receives |
|---|---|---|---|
| `curiosita` | 5 | no cap | a theme a 10-year-old finds interesting (`curiosities`), never one of the last 20; Claude names the Italian Wikipedia article and its photo goes on the blackboard |
| `notizia` | 2 | 3 | the news not yet told; if none is interesting it skips |
| `meteo` | 2 | 2 | forecast and comparisons; only a real change, otherwise it skips |
| `casa` | 1 | 2 | who is home, agenda, room temperatures, today's events, memories |
| `ricordo` | 1 | 1 | the long-term memory |
| `domanda` | 1 | 1 | a question on a theme |
| `aerei` | 1 | 1 | the nearest plane (only if there is one) |

The caps change with `director_topics_max` (for example `{curiosita: 0}` turns curiosities off).
Long-term memories are sent only for `ricordo` and `casa`. Lines never start with the listener's
name; lines with Claude's corrections ("no, aspetta") and lines with degrees, percentages or km/h
not found in the data are discarded; the current time is removed.

Topics already said today (tomorrow's weather, updates, current temperatures, Claude usage, planes)
are recognised from the text and not repeated; temperatures come back only if they changed by 2
degrees or 3 hours have passed, or if you ask.

## Events it reacts to

| Event | Line |
|---|---|
| someone arrives | a greeting, by Claude (people arriving together: one greeting) |
| someone leaves | "Fuori casa: Anna e Mario." (grouped) |
| rain soon / rain stops / strong wind | a warning (rain stop only if it really stopped) |
| forecast change | "Domani 5 gradi in meno di oggi" (once a day) |
| morning | greeting with today against yesterday |
| plane overhead | airline, type, altitude, route |
| holiday, birthday | a line and the costume |
| a room changing fast | "Studio: 2 gradi in meno in mezz'ora. Finestra aperta?" |
| Claude session low / refilled | with `sensor.claude_usage_*` |
| `coinquilino_say` | whatever Home Assistant sends ([details](home-assistant.md)) |

## Memory

- **Today's events**: arrivals, departures, warnings, chats, what Home Assistant asked to remember
  (`remember`). Used for the director and the diary.
- **Diary**: from `diary_at` (21:00) it writes a few lines about the day; tomorrow it shows it in the
  showcase.
- **Long-term memory**: every night at `night_job_at` (03:30) Claude rewrites the list of memories
  with what is worth keeping for weeks: people's tastes, plans, things in progress. It knows the
  character's current age, and leaves out descriptions of itself, people's comings and goings, device
  names, requests about the software.
- In the chat:
  - *"ricordati che Anna ha la verifica venerdì"* — adds a memory;
  - *"dimentica la verifica"* — removes it;
  - *"non parlare più di aerei"* — blocks an interest for good (memories about it go too);
  - *"puoi riparlare di aerei"* — unblocks it.

## Character and interests

Traits (curious, ironic, chatty…) and interests shift a little every Sunday night, depending on what
you liked: the 👍/👎 buttons (`feedback_up` / `feedback_down`, or under Telegram messages) and
whether you answer what it says. It also learns a few curiosities each week, said as "Lo sapevi
che…" and kept in the showcase. Running jokes it repeats too often are detected and forbidden.

## It writes first

With `spontaneous: true`, at most once a day, by day: an idea for something new it could do or a
question to get to know the family, both prepared at night; on Sundays a summary of the week. Ideas
get 👍/👎 and are listed in `apps/proposte.md`. `ideas_avoid` lists topics it must not propose ideas
about. It never proposes watching people (return times, who goes out with whom).

All spontaneous phone messages share one cap: one every `message_gap_hours` (3), never at night.
Reminders and what Home Assistant sends always pass.

## Claude and costs

- Lines are written by `model` (Claude Haiku 5.5): short calls with reasoning off and low effort,
  stopped as soon as the sentence closes; the night work goes through the Batch API at half price.
- Claude is called only while someone in `presence` is home and awake — chat answers always.
- Hard caps: `claude_max_per_hour` (20), `claude_max_per_day` (150), counted across restarts. Over
  the cap it uses built-in lines and says so once in the log.
- Spending is counted with `api_price_in` / `api_price_out` into `sensor.<instance>_costo_api`;
  with `api_budget_month` it warns at 80%.
- Typical use: a few dozen calls a day, 2–4 thousand input tokens each (a chat message with the MCP
  server about 8–9 thousand, for the tool list and the house): well under a dollar a month.
- Without a key everything works with built-in lines (no director, no drawings, no diary by Claude).
