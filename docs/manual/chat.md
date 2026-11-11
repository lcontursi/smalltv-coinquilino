# Chat, Telegram and voice

[Manual](README.md) · [Italiano](../manuale/chat.md)

## Writing to it from Home Assistant

Create a *Text* helper (max length 255), e.g. `input_text.parla_con_alessio`, set it as
`chat_entity` and put it on a dashboard. Write, press enter: the answer appears on the cube (and,
with `chat_reply_phone: true`, on the phone). `chat_from` says who is writing (default: `owner`).

Answers are by Claude, with the recent conversation, what the character knows, and — when you ask
about the house — what Home Assistant's Assist tools say about the exposed devices (or, with the
list, the lights that are on, temperatures and the entities in `control`). Without a key
only the commands below work.

### Commands that don't need Claude

| You write | It does |
|---|---|
| *ricordati che …* | adds a long-term memory |
| *dimentica …* | removes matching memories (and blocks an interest, if it is one) |
| *non parlare più di …* / *puoi riparlare di …* | blocks / unblocks an interest |
| *ricordami di … alle 18* / *tra 20 minuti* / *domani alle 9* | a reminder (in the to-do list, if `reminders_todo`) |
| *fatto …* / *ho fatto …* | ticks off the matching to-do item |

## Telegram

1. Create a bot with @BotFather.
2. Add Home Assistant's **Telegram bot** integration, platform **Polling** (nothing exposed to the
   internet), with the token; add each allowed chat ID (ask @id_bot).
3. Send `/start` to the bot, then list the same IDs in the personal file:

```yaml
telegram_chats:
  123456789: Zio Mario
  987654321: Zia Anna
telegram_commanders: [123456789]   # who may command the house (default: the owner's chat)
```

Then:

- every message gets an answer, by Claude, as "Zio Mario" or "Zia Anna";
- warnings, reminders, ideas and the Sunday summary arrive there (`telegram_notify: true`), with
  👍/👎 buttons; `notify:` stays as a fallback;
- `/aiuto` says what it can do; `/foto` says how many photos are in the album;
- a photo sent to the bot goes into the album; reply «togli» to it to remove it;
- `telegram_aloud: true` also says the answers out loud at home;
- `telegram_event` / `telegram_bot` are needed only with more than one bot.

The bot should be used only by the character.

## Commands to the house

There are two ways. The recommended one uses Home Assistant's own **MCP server**; the other a list
of entities in the personal file.

### With Home Assistant's MCP server (recommended)

1. In Home Assistant add the **Model Context Protocol Server** integration (*Settings → Devices &
   services → Add integration*). In its options keep only **Device control**; leave *Read-only* off,
   or commands won't be offered.
2. Choose which devices the character may see and command where you already do it for voice
   assistants: *Settings → Voice assistants → Expose*.
3. Create a long-lived access token (your profile → *Security*) and set:

```yaml
ha_mcp_url: http://homeassistant.local:8123/api/mcp
ha_mcp_token: !secret ha_mcp_token
control_confirm: [climate]
```

Then in the chat Claude gets Home Assistant's Assist tools: it reads the live state of the exposed
devices (and to-do lists) by itself, and uses names, areas and aliases as you set them in Home
Assistant. Before running a command the character applies its own rules: a yes/no from outside the
house, for the domains in `control_confirm`, for more than 3 commands, for a whole area or domain
without a device name, and for announcements in the house. It says "done" only when Home Assistant
reports which devices it changed and, for on/off, after reading the new state back. Every request,
confirmation and result is in the log (`home.read`, `home.confirm`, `home.action`).

**Names.** Devices are found by the name you see in Home Assistant (and by the aliases you give them
in *Voice assistants → Expose*). Before running a command the character checks that the name exists:
if Claude used a longer one that contains it (the device name in front, for example), it is
corrected on the spot; otherwise Claude gets the most similar exposed names back and tries again.
Nothing runs until the name is right.

**"Spegnila".** Commands with a pronoun — *accendila*, *spegnila*, *alzala* — act on the last device
named; the last command done in the house in the past 30 minutes is part of what Claude receives.

Try it: *"la luce della scrivania è accesa?"* (a read), then *"accendi la luce della scrivania"* and
*"spegnila"*.

### With a list of entities

With a `control:` whitelist (and no `ha_mcp_url`), the chat (and Telegram, from `telegram_commanders`) can switch lights
and set climates:

```yaml
control:
  - light.*
  - climate.living_room
control_confirm: [climate]          # these domains ask "Devo…? sì/no"
control_switch: input_boolean.alessio_comandi
control_verify_seconds: 8
```

- *"spegni la luce dello studio"*, *"metti il salone a 20 gradi"*, *"accendi tutte le luci della
  cucina"*.
- Questions work without a list: *"chi c'è in casa?"*, *"la luce dell'ingresso è accesa?"*, *"quanti
  gradi ci sono nello studio?"*.
- It asks for a yes/no for the domains in `control_confirm`, for more than 3 entities, and whenever
  the person is outside the house.
- It says "done" only after reading the new state back (within `control_verify_seconds`); if Home
  Assistant refuses, it says so. A climate that rejects `turn_off` is set to mode `off` instead.
- Only the entities in the list, only lights and climates. News and other outside text never reach
  the command tool.

## Reminders

- *"ricordami di chiamare la nonna alle 18"*, *"ricordami tra 20 minuti di spegnere il forno"*,
  *"ricordami domani alle 9 della riunione"*.
- With `reminders_todo` the reminder becomes an item with a due time in that list; you also see it in
  the Home Assistant app and can add reminders from there, from Assist or from Alexa.
- When due: on the cube (even at night) and on the phone, always — reminders are never blocked by
  the message cap.

## Siri and CarPlay

Siri can't find a Telegram bot by name ("manda un messaggio ad Alessio" fails). Instead:

1. On the iPhone, in *Shortcuts*, make a shortcut named **Alessio**: *Dictate text* → Home Assistant
   app action *Perform action* `input_text.set_value` on your `chat_entity`, value = the dictated
   text.
2. Set `chat_reply_phone: true`: the answer also arrives as a phone notification (Telegram, or
   `notify`), which CarPlay reads aloud.

"Hey Siri, Alessio" → dictate → the answer is read to you. With an Echo Auto, *"Alexa, aggiungi …
alla lista delle cose da fare"* fills Alexa's to-do list, which `reminders_todo` can read.

## Voice

```yaml
voice_player: media_player.study
voice_tts: tts.edge_tts            # any tts.* entity
voice_language: it-IT-ElsaNeural
voice_options: {pitch: "+80Hz", rate: "+8%"}
voice_volume: 0.5
voice_switch: input_boolean.voce_alessio   # off = silent, the cube still talks
voice_kinds: [person.arrive, chat.reply, plane.overhead, holiday, director, diary,
              weather.rain_soon, weather.wind, say, me.reminder, home.action]
```

Only the kinds in `voice_kinds` are said aloud, never at night (except answers and reminders), and
never over the doorbell (`quiet_seconds`). Cloud engines (Google Translate, Edge TTS) send the
sentence to Google/Microsoft; local ones (Piper) don't. `voice_volume` on a PC changes the system
volume.
