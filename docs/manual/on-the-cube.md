# On the cube

[Manual](README.md) · [Italiano](../manuale/sul-cubo.md)

The cube shows a 240×200 picture drawn in Home Assistant and sent over Wi-Fi to glimmer's Pixel
channel. What you see:

## The speech bubble

Each line appears in a bubble, split into pages that turn every 4.5 seconds; the character's mouth
moves while it "talks".

- A line stays `show_minutes` (20) or until something else comes. A **long text** (the diary, a
  long answer) keeps turning its pages for all that time — the mouth moves only on the first two
  rounds — so whoever walks by later can still read it all.
- At night lines go away after two minutes, except answers to you.

## The blackboard

Next to Alessio, a little board with:

- the **week's weather** (3 days before, today, 3 after) and, when rain or gusts are due, the
  **hourly chart**;
- the **radar** of the planes around the house;
- Claude **usage** charts (with `sensor.claude_usage_*` sensors);
- today's **drawing**, a scene Claude draws with simple shapes like a 10-year-old with felt-tip pens
  (at most every `drawing_hours`), on a theme from `curiosities`;
- the **gallery** of recent drawings.

`cards: false` turns it off.

## Full-cube screens

With `screens: true` (default), whole-cube images:

- **weather**: the week compared with the days before;
- **home**: who is in, room temperatures with the change in the last hour, lights on;
- **power**: with `power_sensor` (W) and `energy_sensor` (kWh since midnight), now and today against
  yesterday.

Blackboards and screens stay until something else replaces them (`show_minutes`, at least
`card_seconds`).

## Today's showcase

What the character made or worked out today comes back in turn when there is nothing new: the week's
chart, the house and power screens, today's drawing, the curiosity of the day, the diary (yesterday's
until tonight's is written), the director's best lines of the last 3 hours (not the ones with current
temperatures, which get old).

- Each thing comes back at least 20 minutes after it was shown; if the cube shows only the face, 6.
- With only the face on the cube, the next free line comes after 1 minute.

## Free chatter

Lines built from data without Claude, chosen in turn: current weather, forecast, home status, who is
in, news, sun, the day, planes nearby, a curiosity, agenda, API usage, the showcase. Each kind has a
minimum interval and a daily cap, spread over the waking hours so the evening still has something to
say; the same identical sentence doesn't come back within 3 hours. Change the caps with
`chatter_day_max` (names as in the log: `news.headline`, `weather.now`…).

## Family photos

Send a photo to the Telegram bot: it appears at once almost full screen in the blackboard's frame,
then comes back in turn every `photo_every_minutes` (30) for `photo_seconds` (40), each photo at most
`photo_day_max` (3) times a day, never at night. Up to `photo_max` (50) are kept, the oldest are
removed.

- The album is `/media/coinquilino` (`photo_dir`): manage it from Home Assistant's *Media* panel.
- From the dashboard: choose one (`photo_select`), show it now, remove it.
- On Telegram: `/foto` says how many there are; reply «togli» to a photo you sent to remove it.
- Photos never leave your home: they are not sent to Claude.

## The room

With `scenes: true` Alessio's room changes: season colours and window, real fog and snow from the
weather, a little calendar with the date, a different object on the shelf every day taken from the
character's interests. Planes overhead are seen through the window.

## Holidays and costumes

Halloween, Christmas, New Year, Easter, birthdays (`birthdays`) and your patron saint
(`local_feast`) bring costumes and decorations, and a line the first time in the day. `feste: false`
turns them off.

## Mood

The face follows a mood: `happy`, `welcome` (someone arrived), `rain`, `sleep`, `tired` (Claude
session above `tired_at`), `moto` (a day for the bike: `moto_days` with the right temperature). The director can
set it for a few minutes; `mood` in `coinquilino_say` too.

## Night

From `night_start` to `night_end`:

- `night_clock: alessio` (default) — its own dark clock: big time, the date in Italian, the moon,
  a few stars, Alessio asleep in a corner; it changes once a minute;
- `night_clock: glimmer` — glimmer's night face;
- `night_clock: off` — the room dimmed by `night_dim`.

It keeps quiet until morning (answers to you still arrive); warnings marked `night: defer` are told
at wake-up.

## Bandit

`character: bandit` replaces Alessio with a pixel-art motorcycle: same functions, its own lines, no
growing up.
