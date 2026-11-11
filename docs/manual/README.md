# Coinquilino — user manual

[Italiano](../manuale/README.md) · [Back to the project](../../README.md)

Coinquilino is an AppDaemon app for Home Assistant that gives your home a character — Alessio, a
10-year-old, or Bandit, a motorcycle — living on a GeekMagic SmallTV Ultra. Home Assistant decides
what matters; the character shows it on the cube, writes it on Telegram and, if you like, says it
out loud.

This manual describes every function and every option. The short version is in the
[README](../../README.md).

## Contents

1. [Installation](installation.md) — firmware, AppDaemon, the app, the settings file, first start.
2. [Configuration](configuration.md) — how settings are read, and every option grouped by topic.
3. [Home Assistant integration](home-assistant.md) — the `coinquilino_say` event, the blueprints,
   to-do lists and calendars, the sensors it publishes, the dashboard, more than one cube.
4. [On the cube](on-the-cube.md) — speech bubble, blackboard, full-cube screens, today's showcase,
   photos, the room, holidays, night.
5. [The character](character.md) — the director, free chatter and its caps, memory and diary,
   character and ideas, Claude and costs.
6. [Chat, Telegram and voice](chat.md) — writing to it, Telegram, commands to the house, reminders,
   Siri and CarPlay, the voice.
7. [Privacy and safety](privacy.md) — what leaves your home, the safeguards.
8. [Log and troubleshooting](troubleshooting.md) — reading the log, common problems.

## In one picture

```
 Home Assistant ──────────────► Coinquilino (AppDaemon) ───── HTTP ─────► SmallTV Ultra
  people, weather, sensors        decides when to talk,                    (glimmer + Pixel
  to-do lists, calendars          renders 240×200 frames,                   channel) shows
  automations / blueprints ──►    asks Claude for the lines                 the frames
   coinquilino_say event          (optional), Telegram, TTS
                       ◄──────── sensors: mood, memories, last line, API spending
```

## Words used in this manual

| Word | Meaning |
|---|---|
| **line** | one sentence the character says, in the speech bubble |
| **blackboard** | the little board next to Alessio with a chart, a radar or a drawing |
| **screen** | a full-cube image (the week's weather, the house, the power) |
| **chatter** | a free line built from data (weather, home, news…), no Claude |
| **director** | the periodic Claude call that picks what is worth saying |
| **showcase** | today's things (charts, drawing, diary, good lines) that come back in turn |
| **personal file** | `coinquilino_personale.yaml`, your settings, never published |
