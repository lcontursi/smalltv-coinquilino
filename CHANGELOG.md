# Changelog

## 3.1.0

- **The director has a topic each turn.** It used to choose freely among everything it knew and
  chose weather and the motorbike almost every time (15 of 28 lines in a day). Now each turn draws a
  topic (a curiosity, a news item, the weather, the house, a memory, a question, a plane) with a
  weight and a daily cap (weather twice, news three times, a memory once), and Claude receives only
  the data for that topic. Long-term memories go to the director only for the memory and house
  topics. If there is nothing worth saying (no interesting news, no real weather change) it skips.
  New options: `director_topics_max`, `curiosities`.
- **Curiosities with a photo.** The most frequent topic: something a 10-year-old finds interesting
  (animals, space, inventions, records...), with themes that don't repeat. Claude names the Italian
  Wikipedia article and its picture goes on the blackboard; the curiosity comes back in the showcase
  for 12 hours.
- Lines no longer start with the listener's name ("Zio Mario, ..."), and news items lose the fixed
  "la notizia più utile..." opening.
- Lines where Claude corrects itself ("no, aspetta...", "non ripeto la formula") are discarded.
- Arrival greetings and director lines are discarded if they contain degrees, percentages or km/h
  that are not in the data (a parcel and 12 degrees were invented on 12/11); arrivals are told to
  use only the facts given.
- The current time is removed from lines ("oggi alle 17:14 le previsioni..."), so they don't come
  back hours later with an old time.
- Long-term facts not confirmed for 10 days are forgotten (habits and preferences stay).
- The MCP chat caches Home Assistant's tools and the instructions (prompt caching): every round
  after the first pays a tenth for that part.

## 3.0.5

- A sentence that takes more than one page now stays on the cube for `show_minutes`, like a short one,
  with its pages turning (the mouth moves only on the first two rounds): before, it disappeared after
  about a minute and left the plain face until the next thing to say.

## 3.0.4

- Commands with a pronoun ("spegnila", "alzala") refer to the last device named or the last command:
  the last command done in the house (within 30 minutes) is given to Claude, and the chat rules say
  to act on it.

## 3.0.3

- A wrong device name that contains the real one (Home Assistant's long name) is corrected on the
  spot, without another Claude round; otherwise Claude gets the most similar exposed names back.

## 3.0.2

- A command with a name Assist doesn't know (for example Home Assistant's long device-plus-entity
  name left in the chat) is checked before running: Claude gets the error back, reads the exact
  names with GetLiveContext and tries again; nothing runs until the name is right.

## 3.0.1

- Answers to commands use the name the person used ("Fatto: ho acceso Luce Scrivania"), not Home
  Assistant's long device-plus-entity name: that name stayed in the chat, Claude reused it for the
  next command ("spegnila") and Assist could not match it.

## 3.0.0

The character becomes a client of Home Assistant's own MCP server.

- **Commands to the house through MCP**: with `ha_mcp_url` and `ha_mcp_token` the chat gives Claude
  the Assist tools of Home Assistant's *Model Context Protocol Server* (Device control): the devices
  exposed to voice assistants, with Home Assistant's names, areas and aliases, plus live state and
  to-do lists. Read-only tools run at once (up to 3 rounds); commands pass the character's own rules
  — a yes/no from outside the house, for `control_confirm` domains, more than 3 commands, a whole area
  or domain, announcements — and "done" comes only from the devices Home Assistant reports as changed,
  with the new state read back for on/off. Every read, confirmation and command is logged.
- The `control` list still works without `ha_mcp_url`.
- New module `hamcp.py` (Streamable HTTP, long-lived token, session renewal): copy it with the others.

## 2.2.3

- **The cube stays busy in the morning too**: with only the face showing, the showcase picks the
  item seen least recently (at least 6 minutes ago) instead of waiting 20, and the next try comes
  after 1 minute instead of 3. The director's lines join the showcase for 3 hours, unless they carry
  current temperatures or Claude usage.

## 2.2.2

- The API spending sensor is published every 5 minutes, not only after a Claude call: after a Home
  Assistant restart the dashboard showed "Entity not found".
- Dashboard example: "what it did at home" is now a logbook of the `coinquilino_*` automations;
  the old list of actions shows only commands from the chat.

## 2.2.1

- **Long-term memories grow up with the character**: the nightly rewrite now knows today's age and
  drops memories from the toddler days (dummy, "nipotino"). It also keeps out what is not worth
  remembering: descriptions of itself and what it can do, people's comings and goings and times,
  device names and commands, requests about the software.

## 2.2.0

The character becomes an extension of Home Assistant instead of an app shaped around one house.

- **House rules move to Home Assistant**: lights left on in an empty house, climate off with an
  open window (and back on), the doorbell nobody answered, low batteries and available updates are
  now blueprints in `blueprints/` (plus two new ones: someone on the way home with Proximity, and
  parcels with 17TRACK). The old options (`doorbell`, `doorbell_open`, `windows`,
  `lights_off_when_empty`, `battery_threshold`…) only log a warning; "aspetto un pacco" is gone.
- **One standard event**: `coinquilino_say` gains `away`, `night`, `wait`, `key`/`repeat_hours`,
  `remember`, `quiet_seconds` and `expect_arrival`; a script blueprint fires it from any
  automation.
- **Reminders and calendars from Home Assistant**: `reminders_todo` (to-do lists, e.g. Local To-do
  or Alexa's) and `calendars`; items with a time and upcoming appointments (`calendar_minutes`) are
  said and sent to the phone, the rest goes into the context and a daily "agenda" line. Chat
  reminders go into the list; "fatto …" ticks an item off. `workday` tells working days.
- **Siri and CarPlay**: `chat_reply_phone` also sends chat answers to the phone, so a Siri shortcut
  writing into `chat_entity` gets its answer read aloud in the car.
- Night ideas never propose watching people (return times, who goes out with whom).

## 2.1.1

The cube is tiny and you look at it by chance: it was mostly showing the bare face.

- **Blackboards and full-cube screens stay** until something else replaces them (`show_minutes`,
  at least `card_seconds`), instead of 40 seconds: the week's chart was gone before you could read it.
- **No empty cube**: when only the face is showing, the next free line comes after 3 minutes instead
  of `talk_every_minutes`, and the showcase is tried first; it has no daily cap and an item comes
  back after 20 minutes instead of 45.
- **Today's diary in the showcase**: once the evening diary is written it replaces yesterday's.

## 2.1.0

From the first day of 2.0 on the cube: it kept saying the indoor and outdoor temperatures, told
tomorrow's weather four times, and whatever it made (a drawing, a chart) was seen once or never.

- **Today's showcase**: drawings, the week's chart, the full-cube screens, the curiosity of the
  day and yesterday's diary go into a daily list that comes back in turn, for free, when there is
  nothing new to say. Curiosities used to disappear after being said once.
- **No repetitions**: topics already said today (tomorrow's weather, Home Assistant updates,
  current temperatures, Claude usage, planes) are recognised from the text and given to the
  director; the weather-change alert, the forecast chatter and the blackboard caption stay quiet
  about tomorrow once it was said; the home chatter no longer repeats an update just announced.
- **Temperatures only when useful**: they reach Claude only when not said in the last 3 hours,
  changed by 2 degrees or more, or asked in chat. Claude usage only from 50% up.
- **Chatter spread over the day**: each daily cap is spent in proportion to the waking hours, so
  the evening is not left with photos only; news down from 8 to 5 a day.
- **Photos**: each photo at most `photo_day_max` (3) times a day.
- **People**: people leaving together get one line, like arrivals; plural fixed lines ("eccovi a
  casa"); an arrival always asks Claude even if the presence sensor lags; the log says why a
  fixed line was used.
- **Director**: it is queued only when it can speak at once (it used to wait 13-14 minutes behind
  the gap and then be dropped); no more "dicevo prima" or announcing a useful fact; today's past
  events are marked as past.
- **Lines**: Claude replies start with a capital letter; the persona forbids inventing things it
  never did (the "stelline gialle" drawing); plane lines without "Brummm!", the radar says which
  plane and how far; "Si azzera alle" instead of "Si riempie alle" for Claude's reset time.

## 2.0.0

After a few weeks of use the character was "too silly" and "always doing the same things". This
version makes it useful first, and lets it change from day to day.

- **Useful first, a ten-year-old**: Alessio no longer starts at 2 years old and grows: he is 10
  (`age`, fixed; `grow: true` brings back the old growth). The persona asks for a concrete piece
  of information in every line (a number, a time, a difference from yesterday, something to do),
  dry irony, no baby talk, no empty enthusiasm. The fixed lines, the director, the diary and the
  chatter were rewritten in the same tone. Gone: the dummy and the "baby bottle" (Claude's usage
  and the API spending are now just "Claude" and "API spending"; the tired mood shows a flat
  battery).
- **He looks his age**: from 8 up Alessio has real hair with a side fringe, eyebrows, a longer
  face, smaller eyes and cheeks, a half smile and a T-shirt. Below 8 he is still the sticker baby.
- **Weather compared with the past days**: Open-Meteo now gives the last 7 days and the next 3
  (`past_days`). The blackboard shows the **week** (3 days before, today highlighted, 3 after:
  sky icon and min-max bar) instead of the next 12 hours, which only come back when rain or gusts
  are due. New lines say what changes: "Domani 5 gradi in meno di oggi", "Dopo giorni asciutti,
  pioggia in arrivo giovedì", "Da domani torna il sereno, dopo 3 giorni di pioggia", warmer or
  colder than the last days. The morning greeting says today against yesterday; once a day, from
  the afternoon, a change in the coming days is announced (`weather.change`). Sunrise and sunset
  come with the hours of daylight and the difference from a week ago.
- **A room that changes every day** (`scenes`): the season tints the walls and shows at the window
  (leaves, blossoms, frost, summer sun), the window shows real fog and snow, a little calendar shows
  today's date, and the object on the shelf changes every day among the character's interests
  (rocket, cat, boat, radio, dinosaur, ball, globe, the toy motorbike; books or a plant on Sundays),
  never a blocked one.
- **Full-cube screens** (`screens`): the week's weather, the house (who is home, room
  temperatures with the change in the last hour, lights on) and, with `power_sensor` /
  `energy_sensor`, the power now and today's energy against yesterday's.
- **The house that changes** (`room_change_degrees`, 1.5): a room getting warmer or colder fast is
  mentioned ("Studio: la temperatura è salita di 2 gradi in un'ora"); a 2-degree drop in half an
  hour asks "Finestra aperta?". Once every 3 hours per room.
- **Fewer repeats**: a news item is read at most once a day (it came back every 3 hours: the same
  local story 6 times on 4 November); each kind of chatter has a daily cap (`chatter_day_max`);
  photos every 30 minutes instead of 10.
- **Doorbell** (`doorbell`, `doorbell_open`, `doorbell_minutes`): if it rings and nobody opens within
  2 minutes, Alessio says so on the cube and sends it to Telegram (outside the message cap). He keeps
  quiet for a minute after a ring (`doorbell_quiet_seconds`), knows today's rings and openings
  ("è passato qualcuno?"), and greets right away who comes in after the door was opened from the
  intercom (the delay is logged, to measure it). *"Oggi aspetto un pacco"* in the chat: a ring with
  the house empty is reported at once, and in the evening he tells you if nobody came.
- **Night alerts wait for the morning**: at night a warning is no longer dropped: it is kept and
  told at wake-up on the cube, the voice and Telegram ("Stanotte alle 2:40 hanno suonato…").
- **Low batteries for the whole house** (`battery_threshold`, 20; `battery_exclude`): one warning
  per device until the battery goes back up; several together in one line; to the phone when
  nobody is home. It used to repeat every day below 15%.
- **`coinquilino_say` with `telegram: true`** also sends the line to Telegram through the bot.

## 1.9.0

- **"dimentica gli aerei" now really does it**: when the text names one of the character's
  interests ("gli aerei", "non parlare più di aerei"), the interest is dropped, the weekly update
  can't raise it again, and the prompt says not to talk about it. The answer tells what was done
  ("non parlo più di aerei"). "puoi riparlare di aerei" undoes it.
- The nightly memory pass no longer turns chat commands (ricordati / dimentica / ricordami) into
  memories, and is told to drop memories about blocked topics.
- The nightly idea is checked in code: a "function" idea that repeats something already built
  (lights off in an empty house, window and heating, rain warnings, weekly summary, night clock…)
  is discarded, logged as SKIP and passed back as "already known" the next night.

## 1.8.1

- Forbidden catchphrases are cut from the line itself when Claude writes them anyway ("…, booo!
  Ti voglio tanto bene!"), unless nothing would be left.
- The weekly summary gets the same rules (no catchphrases, no plane counts, no reproaches).
- The nightly idea knows what the character already does (autonomy, rain warnings, weekly
  summary, night clock), so it doesn't propose it again.
- More sad news filtered (persecutions, expulsions, deportations); 1 November is "Ognissanti".

## 1.8.0

- **Alessio's own night clock** (`night_clock: alessio`, the new default): rounded big time, the
  date in Italian, moon, stars and Alessio asleep in a corner, dark and dim; redrawn once a
  minute (only the changed part travels), and the cube is brought back to the Pixel channel if it
  wanders off. `night_clock: glimmer` keeps the 1.4.1 behaviour, `off` the dimmed bedroom.
- **"It stopped raining" only when it really did**: two dry Open-Meteo checks in a row (~30 min)
  and Home Assistant's weather entity not rainy; re-checked when it is about to be said.
- **Telegram buttons**: after 👍/👎 or Sì/No the buttons are replaced by what you chose
  (`edit_replymarkup`), one vote per message, a second Sì does nothing.
- **Autonomy checks the result** like the chat commands: lights and climate are reported as done
  only when their state changed (climate falls back to `set_hvac_mode: off`); actions run in a
  thread, so AppDaemon is not blocked while waiting.
- **Memories without catchphrases**: the nightly memory job is told not to store how the
  character speaks (and which phrases are forbidden). **Ideas** see the votes of past ideas and
  avoid topics in `ideas_avoid`.
- The dashboard's "actions" list shows only actions on the house, not messages.
- Moving the album between folders on different disks works (`shutil.move`) and logs failures.

## 1.7.0

- **Photo album you can manage**: it moves to `/media/coinquilino` (`photo_dir`) when the AppDaemon
  add-on can see `/media` — so Home Assistant's *Media* panel shows it, and pictures added there
  are prepared and joined to the rotation; deleted ones leave it. Dashboard: an `input_select`
  with the photos plus "show now" / "remove" buttons. Telegram: reply «togli» to a photo you sent
  to remove it, `/foto` says how many there are (only `telegram_commanders`).
- **Photos with their own colours** (`photo_saturation`, 1.1, instead of the character's 1.4).
- **Tone**: a catchphrase stays forbidden for 7 days once spotted; the character's look is in
  the data only when someone asks (or the holiday costume, once a day); the nightly idea gets
  the same rules.
- **News**: lottery and winnings (lotto, gratta e vinci, jackpot…) are dropped as ads; funerals and
  cemeteries count as sad; the director marks the headline it used (`<notizia>N</notizia>`),
  which then leaves its data for the day and the chatter for 3 hours.
- Memory is saved when AppDaemon stops the app (no repeats after a restart); with the cube
  unreachable the channel warning appears at most every 30 minutes.

## 1.6.0

- **Family photos from Telegram**: Home Assistant's bot downloads the photo (`download_file`,
  named `coinquilino_*`), the app takes it from `/homeassistant/telegram_bot` (or `photo_inbox`),
  prepares it (landscape cropped, portrait whole on a blurred background) and shows it right away
  in a big version of the blackboard frame. Then a photo every 10 minutes for 40 seconds, in turn,
  never at night; at most 50 kept. Photos never leave the house.
- **Writes first**: at night it prepares an idea for something new it could do, or a question for
  the family; by day (10-20) at most one a day goes to Telegram, with 👍/👎, and all ideas are
  listed in `proposte.md`. On Sundays, a summary of the week (from the weekly character job).
- **One cap for every spontaneous message** (`message_gap_hours`, 3): warnings, actions, ideas,
  summary; never at night. Reminders you asked for always go through.
- **Fewer planes** (`plane_topic_minutes`, 60): at most one plane topic an hour across chatter,
  overhead announcements and the director; the daily plane count is only for the diary.
- **Dashboard**: `sensor.alessio_stato` (mood, age, holiday, memories, character, reminders,
  last actions, ideas, photos) and a ready view in `examples/plancia.yaml`; optional live preview
  of the cube (`preview`).

## 1.5.1

- **"Done" only when it is done**: after every house command the app waits for the entity's
  state to change (`control_verify_seconds`, 8). AppDaemon does not hand service errors back to
  the caller, so a refused command used to be reported as done. Now it says what failed and logs
  a `SKIP` with the reason.
- **Climates that refuse turn_off/turn_on** are retried with `climate/set_hvac_mode` ("off", or
  the last mode they were in). "Accendi in caldo/freddo/auto/deumidifica/ventola" picks the mode.
- **No more catchphrases**: phrases repeated in the last Claude-written lines ("booo", "ti voglio
  tanto bene") are listed to Claude as forbidden; output rule against fixed closings.
- **Holiday costume**: once mentioned today to everyone at home, the costume is left out of what
  Claude sees (unless someone asks how it is dressed).
- **Nightly job**: 16,000 output tokens (reasoning on), a `CLAUDE` log line with tokens, stop
  reason and cost for batch results too, and a clear message when the answer comes back empty.
- A headline the director told in its own words is not read again by the chatter for 3 hours.

## 1.5.0

- **Talk to your house**: in the chat it answers questions about the house (who's home, lights
  that are on, temperature sensors) and, for the entities in `control` (lights and climates, `*`
  allowed), carries out "turn on/off" and "set to N degrees" through a Claude tool. The app checks
  every action against the list, logs it as `ACT`, and asks "Devo…? sì/no" for `control_confirm`
  domains (climate by default), more than 3 devices, or when the person is away. Free yes/no,
  valid 3 minutes, only from whoever asked. `control_switch` turns commands off.
- **Telegram** through Home Assistant's *Telegram bot* integration: chat with the character from
  anywhere (`telegram_chats`), house commands only from `telegram_commanders`, yes/no as buttons,
  notifications on Telegram with 👍/👎 (the HA `notify` stays as fallback). Replies to Telegram
  messages show on the cube but are not spoken aloud unless `telegram_aloud: true`.
- The holiday costume check matches word stems ("zucchina" counts as the pumpkin).
- Sad-news filter: "violente/violento", fights, threats, beatings.

## 1.4.1

- **Hidden reasoning off for short lines**: Haiku 5.5 thinks by default and bills it as output
  (400–1,200 tokens for a 20-word sentence; two drawings came back empty because reasoning used up
  the whole budget). Real-time calls now send `thinking: disabled` and low effort; the nightly
  batch keeps reasoning. `claude_thinking: true` restores the old behaviour; models that reject the
  parameters are retried without them. An empty answer cut by `max_tokens` is now logged as such.
- **Night belongs to glimmer** (`night_clock`, on by default): at `night_start` the cube switches
  to glimmer's night clock and the app stops sending frames until `night_end`, then brings Alessio
  back. Needs night mode *Dim clock only* on the cube; without it Alessio sleeps on the cube as before.
- **No more repetitions**: a chatter line or headline is not repeated within 3 hours (news already
  read as "new" included); the director gets its own memory of today's topics (kept across
  restarts) and only sees headlines not yet read out.
- **News filter**: `skip` words also match whole words in the title; gambling ads disguised as
  news (casino, slot, betting…) are always dropped.
- "Who's home" chatter uses the same rule as greetings: someone who left less than
  `away_minutes` ago still counts as home (GPS bounce).
- The holiday costume is mentioned at most once a day to the people at home.
- Dollar amounts written the Italian way ("0,01 $ su 2 $").
- The log says when the nightly job is a morning catch-up.

## 1.4.0

- **Long-term memory**: every night the day's events, chats and diary are distilled into at most
  40 memories (facts, habits, running jokes, preferences) that Claude sees in every call. Chat
  commands, free of charge: "ricordati che…", "dimentica…", "ricordami di … alle 18 / tra 20 minuti".
- **Reminders** are said at the right time (also at night) and sent to the phone (`notify`).
- **A character that evolves**: traits and interests change by at most one step a week, driven by
  👍/👎 buttons (`feedback_up`/`feedback_down`) and chat replies; each week it also learns 7
  curiosities that become free chatter. Drawings you 👍 go to a gallery shown again for free.
- **Growth**: Alessio starts at 2 and grows a year every 30 days up to 12 (`start_age`,
  `grow_days`, `max_age`): way of speaking, persona and (no more pacifier) look change with age.
- **Nightly work through the Batch API** (half price), with automatic fallback to normal calls.
- **Autonomy (opt-in, `autonomy: true`)**: lights left on in an empty house are turned off
  (`lights_off_when_empty`), the climate is turned off while a mapped window is open and restored
  when it closes (`windows`), the director may send a phone notification when something matters
  (at most one every 3 hours). Every action is an `ACT` line in the log; `autonomy_switch` stops it.
  Without autonomy the same situations become suggestions.
- **API baby bottle**: the cost of its own calls (tokens × `api_price_in`/`api_price_out`, batch at
  half, cache tokens priced) in `sensor.*_costo_api`, a chatter line with chart, and a warning at
  80% of `api_budget_month`. The `CLAUDE` log line shows the cost of each call.
- Home Assistant updates are now called that ("In Home Assistant ci sono 2 aggiornamenti…").
- Open windows/doors are part of what Claude knows.

## 1.3.0

- **People arriving together get one greeting** (and one Claude call instead of one each):
  arrivals within `arrive_group_seconds` (90) are greeted together.
- Urgent things are said in the order they happened (the first to arrive is greeted first).
- **Fewer output tokens**: Claude is stopped as soon as it closes `</frase>` / `</disegno>`; the
  director's mood is asked before the sentence. If Claude writes text before the tag, the log
  shows it (at most once an hour) with the token count.
- **No chatter in an empty house.**
- More variety: each chatter topic has its own minimum interval (the date every 4 hours, the sun
  every 2…) and the very same sentence doesn't come back within 3 hours. Claude usage is mentioned
  only above 50% of the session or 85% of the week.

## 1.2.0

- **Leaving home is told to who stays** ("Anna adesso è fuori casa"), with a fixed line: no more
  Claude calls for it. Nothing is said if the house is empty (it's only remembered).
- **Indoor temperature as one average** ("In casa ci sono 22 gradi"), from `indoor_temperature:`
  (any temperature sensor or climate) or, without it, from the `climate.*` entities.
- **Planes**: defaults 15 km / 3 km overhead; transponders on the ground (below
  `plane_min_altitude_m`, 150 m, or almost still) are ignored.
- What was already said survives restarts: morning greeting, rain and wind warnings, last lines
  (no more "Buongiorno" twice after Home Assistant restarts).
- Drawings: an unclosed tag or rows off by up to 2 characters are fixed instead of thrown away.
- One director/drawing/diary turn in the queue at a time; leaving and morning go first.
- "Giornata da moto?" only on `moto_days`; Claude usage chatter only when usage is high.
- **New log format** (`SAY`/`QUEUE`/`SKIP`/`CLAUDE`, `free`/`paid`, real token counts) and
  English topic names, also in `voice_kinds` (old names still accepted).

## 1.1.0

- **Spending cap** on Claude calls: `claude_max_per_hour` (20) and `claude_max_per_day` (150),
  chat included, kept across restarts.
- Text coming from outside (headlines, chat, names, flights) is sent to Claude inside
  `<dati>` tags and treated as data, never as instructions.
- `!secret` and `!env_var` in the settings file.
- **More cubes**: settings file < instance in `apps.yaml`; one memory file and one sensor per
  instance; `coinquilino_say` accepts `cube:`.
- Fonts bundled with their OFL licenses: nothing is downloaded at start-up.
- News from any number of RSS feeds (`feeds:`, each with label and categories to skip); no more
  page scraping. `local_feed`/`local_label`/`local_skip` and the `locali` source still work.
- Feeds capped at 2 MB, honest User-Agent.
- Open-Meteo uses the home's time zone instead of a fixed one.
- Clear errors for a missing `host`, an unknown character or a wrong cube token (logged once).
- Saving the settings file restarts the app by itself (AppDaemon doesn't watch that file).
- `voice_switch`: an `input_boolean` on the dashboard mutes the voice (the display keeps talking).
- HACS layout (`apps/coinquilino/`), examples in `examples/`, tests with a fake Home Assistant
  and a fake cube, lint and CI.
- Firmware patch: `/frame` bounds check can no longer overflow; a request without a frame
  gets `400`. Version `0.22.0-glimmer-pixel.2`. Tested on a SmallTV Ultra: both cases are refused
  (`window outside scene`, `missing frame`) and normal streaming is unchanged.

## 1.0.0

- First public version: all personal data moved to `coinquilino_personale.yaml`.
