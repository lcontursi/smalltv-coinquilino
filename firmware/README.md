# Firmware: glimmer + Pixel channel

The cube runs [glimmer](https://github.com/Avinava/glimmer) (MIT), an open firmware for the
GeekMagic SmallTV Ultra (ESP8266, 240×240 ST7789). `glimmer-pixel-channel.patch` adds a
**Pixel** channel that shows frames streamed over HTTP, so a server (here: AppDaemon) can draw
anything on the panel without the ESP8266 having to store images.

The patch is made against glimmer commit `bf7fba4` (October 2026).

## Build and flash

You need git, Python and PlatformIO (`pip install platformio`).

```sh
git clone https://github.com/Avinava/glimmer.git
cd glimmer
git checkout bf7fba4            # or try the latest main
git apply /path/to/glimmer-pixel-channel.patch
python -m platformio run -e nodemcuv2
```

The firmware ends up in `.pio/build/nodemcuv2/firmware.bin` and reports version
`0.22.0-glimmer-pixel.2`. The repository's CI builds the same file on every push.

- **Cube already on glimmer**: open `http://<cube>/update` and upload `firmware.bin` in the
  *firmware* field only. Your settings are kept.
- **Stock cube**: follow glimmer's [FLASHING.md](https://github.com/Avinava/glimmer/blob/main/FLASHING.md)
  first, then update as above.

The Pixel channel is enabled by default (`show_pixel: true`). The web page shows it as
*Coinquilino* only if you also flash the patched filesystem (`littlefs.bin`), which replaces
the device settings — not needed for normal use. While nothing is streaming, the channel shows
a short waiting text.

## Protocol

| request | what |
|---|---|
| `GET /pixel` | `{"active": bool, "seq": N, "x": 0, "y": 30, "w": 240, "h": 200, "age_ms": N, "wait": "..."}` — the scene is the 240×200 area below glimmer's top bar; `active` is true while the Pixel channel is on screen; `seq` increases each time it comes back on screen (the server then resends the whole frame) |
| `POST /pixel` `{"wait": "text"}` | the waiting text shown before the first frame (max 47 ASCII characters) |
| `POST /frame?x=&y=&w=&h=` | multipart field `frame`: raw RGB565 big-endian pixels of a `w×h` rectangle at `x,y` inside the scene (defaults: the whole scene). Painted only while the Pixel channel is on screen, otherwise `409`; a rectangle outside the scene or a request without the `frame` part gets `400` |
| `POST /api/channel` `{"name": "Pixel", "hold_s": N}` | switch to the channel and keep it on screen for up to `N` seconds (≤120) before auto-rotation resumes |

If an API token is set on the device, `/frame`, `/pixel` (POST) and `/api/channel` need it. Sending only the
rectangles that changed keeps animations smooth over Wi-Fi.
