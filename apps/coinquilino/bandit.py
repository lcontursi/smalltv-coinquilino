"""
Bandit — la coinquilina del SmallTV: una moto naked blu anni '90 vista di fronte, in pixel art.

Scena 240x200 (sotto la barra dell'orologio del cubo), disegnata a 80x67 "pixel
logici" e ingrandita x3. Nuvoletta a piena
risoluzione che si mostra solo quando ha qualcosa da dire (a pagine).
Gli occhi sono i due strumenti, il muso e' il faro, le guance le frecce.

render(mood, sky, weather, text, frame, talking, seed, font_path) -> PIL.Image
  mood:    happy | sleep | rain | moto | tired | welcome
  sky:     day | dawn | sunset | night | rain
  weather: None | 'clouds' | 'rain'
  text:    pagina di testo da mostrare nella nuvoletta ('' = nessuna nuvoletta)
  talking: True mentre "parla" (la bocca si muove)
"""
import math
import random

from PIL import Image, ImageDraw, ImageFont

FONT = ("Silkscreen-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/silkscreen/Silkscreen-Regular.ttf")

LW, LH = 80, 67
SCALE = 3
W, H = 240, 200

GROUND = 61             # riga su cui poggiano le ruote

C = {
    "blue_dk": (38, 50, 84), "blue": (62, 80, 124), "blue_hi": (110, 132, 180),
    "blue_shine": (180, 196, 230), "white": (245, 245, 250),
    "black": (24, 24, 30), "seat": (36, 34, 40), "seat_hi": (70, 66, 76),
    "metal_dk": (70, 74, 84), "metal": (140, 146, 158), "metal_hi": (205, 210, 220),
    "chrome": (225, 230, 238), "tire": (30, 30, 34), "rim": (110, 114, 124),
    "lamp": (255, 238, 150), "lamp_off": (120, 120, 105), "red": (226, 50, 50),
    "eye": (20, 20, 40), "blush": (255, 130, 160), "mouth": (20, 20, 40),
    "stone": (226, 205, 160), "stone_lo": (196, 172, 124), "stone_line": (170, 146, 100),
    "road": (70, 72, 80), "road_line": (230, 230, 220),
}

SKIES = {
    #            alto              basso            campanile         stelle
    "night":   ((14, 18, 44),    (40, 42, 92),    (26, 28, 60),     True),
    "dawn":    ((92, 110, 180),  (250, 170, 130), (120, 100, 130),  False),
    "day":     ((70, 150, 225),  (175, 218, 250), (140, 168, 200),  False),
    "sunset":  ((70, 60, 130),   (250, 140, 80),  (90, 60, 90),     False),
    "rain":    ((90, 100, 116),  (150, 158, 170), (110, 116, 128),  False),
}


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------------ sfondo
def _sky(d, sky, rng):
    top, bot, tower, stars = SKIES[sky]
    for y in range(GROUND):
        d.line([(0, y), (LW - 1, y)], fill=_lerp(top, bot, y / (GROUND - 1)))
    if stars:
        for _ in range(34):
            x, y = rng.randrange(LW), rng.randrange(0, 40)
            d.point((x, y), fill=(255, 255, 230) if rng.random() < .7 else (180, 200, 255))
    return tower


def _celestial(d, sky):
    if sky == "night":
        d.ellipse([6, 6, 14, 14], fill=(250, 245, 210))
        d.ellipse([9, 5, 17, 13], fill=SKIES["night"][0])
    elif sky == "day":
        d.ellipse([5, 5, 14, 14], fill=(255, 214, 80))
        for a in range(0, 360, 45):
            x = 9.5 + math.cos(math.radians(a)) * 8
            y = 9.5 + math.sin(math.radians(a)) * 8
            d.point((round(x), round(y)), fill=(255, 214, 80))
    elif sky == "dawn":
        d.ellipse([62, 32, 74, 44], fill=(255, 200, 120))
    elif sky == "sunset":
        d.ellipse([4, 30, 16, 42], fill=(255, 150, 70))


def _city(d, col):
    # un campanile e i tetti della citta', tutto di profilo
    x0 = 8
    d.rectangle([x0, 22, x0 + 8, GROUND], fill=col)
    d.rectangle([x0 + 1, 17, x0 + 7, 22], fill=col)
    d.rectangle([x0 + 2, 12, x0 + 6, 17], fill=col)
    d.line([(x0 + 4, 7), (x0 + 4, 12)], fill=col)
    for y in (26, 33, 40):
        d.rectangle([x0 + 3, y, x0 + 5, y + 1], fill=_lerp(col, (0, 0, 0), .35))
    d.rectangle([0, 46, 26, GROUND], fill=col)
    d.rectangle([54, 44, 79, GROUND], fill=col)
    d.rectangle([62, 39, 70, 44], fill=col)
    d.pieslice([61, 35, 71, 43], 180, 360, fill=col)        # cupoletta


def _clouds(d, dark, rng):
    col = (200, 205, 214) if dark else (250, 250, 255)
    sh = (160, 166, 178) if dark else (220, 228, 240)
    for i in range(3):
        x = 14 + i * 20 + rng.randrange(-3, 4)
        y = 8 + (i % 2) * 6
        d.ellipse([x, y + 1, x + 13, y + 7], fill=sh)
        d.ellipse([x, y, x + 13, y + 6], fill=col)
        d.ellipse([x + 4, y - 4, x + 11, y + 3], fill=col)


def _ground(d, frame, moving):
    d.rectangle([0, GROUND, LW - 1, LH - 1], fill=C["road"])
    d.line([(0, GROUND), (LW - 1, GROUND)], fill=C["stone_lo"])
    d.rectangle([0, GROUND - 2, LW - 1, GROUND - 1], fill=C["stone"])     # marciapiede
    for x in range(0, LW, 8):
        d.line([(x, GROUND - 2), (x, GROUND - 1)], fill=C["stone_line"])


def _rain(d, rng, frame, shelter=None):
    for _ in range(46):
        x = rng.randrange(LW)
        y = (rng.randrange(LH) + frame * 4) % GROUND
        if shelter and shelter[0] <= x <= shelter[2] and shelter[1] <= y:
            continue
        d.line([(x, y), (x, y + 2)], fill=(170, 200, 240))
    for px in (20, 50, 70):                                    # pozzanghere
        d.ellipse([px - 5, GROUND + 1, px + 5, GROUND + 3], fill=(110, 130, 160))


# ------------------------------------------------------------------ la moto (di fronte)
# Il davanti della Bandit e' gia' una faccia: i due strumenti tondi sono gli occhi,
# il faro cromato il muso (la bocca e' sul vetro), le frecce arancioni le guance,
# gli specchietti tondi le antenne.
CX = 40                 # asse della moto

def _eye(d, ex, ey, mood, frame, talking):
    d.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=C["metal_dk"])        # cassa
    d.ellipse([ex - 4, ey - 4, ex + 4, ey + 4], fill=C["chrome"])
    d.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=C["white"])           # quadrante
    blink = frame % 9 == 8 and mood not in ("sleep",)
    if mood == "sleep" or blink:
        d.line([(ex - 2, ey + 1), (ex + 2, ey + 1)], fill=C["eye"])
        d.point((ex - 3, ey), fill=C["eye"]); d.point((ex + 3, ey), fill=C["eye"])
        return
    if mood == "tired":                                                    # palpebre basse
        d.rectangle([ex - 3, ey - 3, ex + 3, ey - 1], fill=C["metal"])
        d.rectangle([ex - 1, ey, ex + 1, ey + 2], fill=C["eye"])
        return
    look = 0 if talking else (1 if frame % 40 < 6 else 0) - (1 if 20 <= frame % 40 < 26 else 0)
    if mood == "moto":                                                     # stelline
        c = (240, 160, 30)
        d.line([(ex - 2 + look, ey), (ex + 2 + look, ey)], fill=c)
        d.line([(ex + look, ey - 2), (ex + look, ey + 2)], fill=c)
        d.point((ex + look, ey), fill=C["eye"])
        return
    d.rectangle([ex - 1 + look, ey - 2, ex + 1 + look, ey + 2], fill=C["eye"])
    d.point((ex - 1 + look, ey - 2), fill=(255, 255, 255))
    if mood in ("welcome", "happy"):                                      # lancetta rossa = brillio
        d.point((ex + 2, ey - 2), fill=C["red"])


def _bike(d, mood, frame, talking):
    bob = 1 if (mood in ("happy", "welcome") and frame % 2) else 0
    if mood == "moto":
        bob = frame % 2                                                    # motore che vibra
    y = -bob
    body, body_hi = C["blue_dk"], C["blue"]

    # motore e collettori dietro alla forcella
    d.rounded_rectangle([24, 40 + y, 56, 52 + y], radius=3, fill=C["metal_dk"])
    for yy in range(42, 51, 2):
        d.line([(26, yy + y), (54, yy + y)], fill=C["metal"])
    for xx in (28, 33, 47, 52):                             # 4 collettori
        d.line([(xx, 50 + y), (xx + (1 if xx > CX else -1) * 2, 58)], fill=C["chrome"], width=2)
    # serbatoio che spunta dietro agli strumenti
    d.rounded_rectangle([22, 24 + y, 58, 36 + y], radius=6, fill=body)
    d.line([(26, 26 + y), (54, 26 + y)], fill=body_hi)
    d.line([(23, 30 + y), (24, 34 + y)], fill=C["blue_shine"])

    # gomma, cerchio e parafango
    d.rounded_rectangle([CX - 4, 48, CX + 4, GROUND], radius=3, fill=C["tire"])
    for yy in range(50, GROUND - 1, 3):
        d.line([(CX - 2, yy), (CX + 2, yy + 1)], fill=(55, 55, 60))
    d.rectangle([CX - 1, 50, CX + 1, 58], fill=C["metal"])
    d.chord([CX - 8, 44 + y, CX + 8, 56 + y], 180, 360, fill=body)
    d.line([(CX - 6, 46 + y), (CX + 6, 46 + y)], fill=body_hi)

    # steli forcella
    for fx in (CX - 9, CX + 8):
        d.rectangle([fx, 30 + y, fx + 1, 52], fill=C["chrome"])
        d.rectangle([fx - 1, 44, fx + 2, 53], fill=C["metal"])             # foderi

    # manubrio, manopole, specchietti tondi
    d.line([(14, 21 + y), (66, 21 + y)], fill=C["black"], width=2)
    d.rectangle([10, 20 + y, 16, 23 + y], fill=C["seat"])
    d.rectangle([64, 20 + y, 70, 23 + y], fill=C["seat"])
    for sx, mx in ((19, 14), (61, 66)):
        d.line([(sx, 21 + y), (mx, 11 + y)], fill=C["metal"])
        d.ellipse([mx - 4, 6 + y, mx + 4, 13 + y], fill=C["metal_dk"])
        d.ellipse([mx - 3, 7 + y, mx + 3, 12 + y], fill=C["chrome"])
        d.point((mx - 1, 8 + y), fill=(255, 255, 255))

    # frecce arancioni (lampeggiano insieme nel benvenuto)
    blink_on = mood == "welcome" and frame % 2 == 0
    for ix, sx in ((22, CX - 9), (58, CX + 9)):
        d.line([(sx, 38 + y), (ix, 38 + y)], fill=C["metal_dk"], width=2)
        col = (255, 200, 80) if blink_on else (232, 120, 30)
        d.ellipse([ix - 3, 35 + y, ix + 3, 41 + y], fill=col)
        d.point((ix - 1, 36 + y), fill=(255, 235, 190))
        if blink_on:
            d.point((ix + (-5 if ix < CX else 5), 38 + y), fill=(255, 210, 90))
            d.point((ix + (-5 if ix < CX else 5), 36 + y), fill=(255, 210, 90))
            d.point((ix + (-5 if ix < CX else 5), 40 + y), fill=(255, 210, 90))

    # occhi = strumenti
    _eye(d, CX - 6, 26 + y, mood, frame, talking)
    _eye(d, CX + 6, 26 + y, mood, frame, talking)

    # muso = faro con la bocca sul vetro
    hx, hy = CX, 38 + y
    d.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=C["metal_dk"])
    d.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=C["chrome"])
    glass = C["lamp_off"] if mood == "sleep" else C["lamp"]
    d.ellipse([hx - 6, hy - 6, hx + 6, hy + 6], fill=glass)
    d.ellipse([hx - 4, hy - 5, hx - 1, hy - 3], fill=(255, 255, 240))      # riflesso
    blush = C["blush"]
    d.rectangle([hx - 6, hy, hx - 5, hy + 1], fill=blush)
    d.rectangle([hx + 5, hy, hx + 6, hy + 1], fill=blush)
    my = hy + 2
    if talking and frame % 2 == 0:
        d.ellipse([hx - 2, my - 1, hx + 2, my + 3], fill=C["mouth"])
        d.line([(hx - 1, my + 2), (hx + 1, my + 2)], fill=blush)
    elif mood in ("happy", "welcome", "moto"):
        d.line([(hx - 2, my + 1), (hx + 2, my + 1)], fill=C["mouth"])
        d.point((hx - 3, my), fill=C["mouth"]); d.point((hx + 3, my), fill=C["mouth"])
    elif mood == "sleep":
        d.ellipse([hx - 1, my, hx + 1, my + 2], fill=C["mouth"])
    elif mood == "tired":
        d.line([(hx - 2, my + 1), (hx + 2, my)], fill=C["mouth"])
        d.point((hx + 3, my - 1), fill=C["mouth"])
    else:
        d.line([(hx - 1, my + 1), (hx + 1, my + 1)], fill=C["mouth"])

    return {"head": (CX - 12, 20 + y, CX + 12, 32 + y), "lamp": (hx, hy)}


def _accessories(d, mood, frame, p):
    hx0, hy0, hx1, hy1 = p["head"]
    if mood == "sleep":
        cap, band = (70, 90, 200), (235, 235, 245)
        d.polygon([(hx0 + 1, hy0 + 2), (hx1 - 1, hy0 + 2), (hx1 + 6, hy0 - 6),
                   (CX + 2, hy0 - 9)], fill=cap)
        d.rectangle([hx0, hy0 + 1, hx1, hy0 + 3], fill=band)
        d.ellipse([hx1 + 5, hy0 - 8, hx1 + 9, hy0 - 4], fill=band)
        zc = (220, 230, 255)
        for i, (zx, zy, sz) in enumerate(((hx1 + 10, hy0 + 4, 3), (hx1 + 15, hy0 - 3, 4),
                                           (hx1 + 21, hy0 - 11, 5))):
            if i <= frame % 4:
                d.line([(zx, zy), (zx + sz, zy)], fill=zc)
                d.line([(zx + sz, zy + 1), (zx, zy + sz - 1)], fill=zc)
                d.line([(zx, zy + sz), (zx + sz, zy + sz)], fill=zc)
    elif mood == "rain":
        hood, hood_dk = (250, 205, 40), (200, 150, 20)
        d.chord([hx0 - 2, hy0 - 6, hx1 + 2, hy0 + 8], 180, 360, fill=hood_dk)
        d.chord([hx0 - 1, hy0 - 5, hx1 + 1, hy0 + 7], 180, 360, fill=hood)
        d.rectangle([hx0 - 2, hy0 + 1, hx1 + 2, hy0 + 2], fill=hood_dk)
        d.line([(hx0 + 3, hy0 - 3), (hx0 + 8, hy0 - 4)], fill=(255, 240, 150))
        return (hx0 - 6, hy0 - 6, hx1 + 6)
    elif mood == "moto":
        hx, hy = p["lamp"]
        if frame % 2 == 0:                                       # faro acceso, fascio
            for dx in (-6, 0, 6):
                d.line([(hx + dx // 2, hy + 9), (hx + dx * 2, GROUND - 1)], fill=(255, 245, 170))
        for i, yy in enumerate((26, 34, 42)):                    # vento ai lati
            ln = 3 + ((frame + i) % 3) * 2
            d.line([(2, yy), (2 + ln, yy)], fill=(255, 255, 255))
            d.line([(LW - 3 - ln, yy + 3), (LW - 3, yy + 3)], fill=(255, 255, 255))
    elif mood == "tired":
        for dx, dy in ((0, 0), (4, 5)):
            yy = hy0 + 2 + dy + (frame % 3)
            sx = hx1 + 3 + dx
            d.point((sx, yy), fill=(140, 200, 255))
            d.rectangle([sx - 1, yy + 1, sx + 1, yy + 2], fill=(140, 200, 255))
        if frame % 2 == 0:                                       # spia riserva
            fx, fy = hx0 - 12, hy0 + 2
            d.rectangle([fx, fy, fx + 5, fy + 7], fill=(240, 160, 30))
            d.rectangle([fx + 1, fy + 1, fx + 4, fy + 3], fill=(255, 230, 150))
            d.line([(fx + 6, fy + 2), (fx + 7, fy + 3)], fill=(240, 160, 30))
            d.line([(fx + 7, fy + 3), (fx + 7, fy + 6)], fill=(240, 160, 30))
    elif mood == "welcome":
        hx2, hy2 = hx1 + 8, hy0 + 2 - (frame % 3)
        heart = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]
        for r, row in enumerate(heart):
            for c, ch in enumerate(row):
                if ch == "X":
                    d.point((hx2 + c, hy2 + r), fill=(240, 70, 110))
    return None


# ------------------------------------------------------------------ nuvoletta
_FONT_CACHE = {}


def _font(path, size):
    k = (path, size)
    if k not in _FONT_CACHE:
        _FONT_CACHE[k] = ImageFont.truetype(path, size)
    return _FONT_CACHE[k]


BUBBLE_W = 210          # larghezza utile del testo
BUBBLE_LINES = 3        # righe per pagina


def wrap(text, font_path):
    """Spezza un messaggio in pagine da BUBBLE_LINES righe."""
    f = _font(font_path, 16)
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= BUBBLE_W:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return ["\n".join(lines[i:i + BUBBLE_LINES]) for i in range(0, len(lines), BUBBLE_LINES)] or [""]


def _bubble(img, page, font_path, more):
    if not page:
        return
    d = ImageDraw.Draw(img)
    f = _font(font_path, 16)
    lines = page.split("\n")
    lh = 17
    bw = int(max(d.textlength(l, font=f) for l in lines)) + 14 + (8 if more else 0)
    bh = len(lines) * lh + 8
    bx, by = max(4, 236 - bw), 4
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=4, fill=(255, 255, 255),
                        outline=(30, 30, 40), width=2)
    tx = min(bx + bw - 20, 140)                                 # codina verso il serbatoio
    d.polygon([(tx, by + bh - 1), (tx + 10, by + bh - 1), (tx + 2, by + bh + 10)],
              fill=(255, 255, 255))
    d.line([(tx, by + bh), (tx + 2, by + bh + 10), (tx + 10, by + bh)], fill=(30, 30, 40), width=2)
    for i, l in enumerate(lines):
        d.text((bx + 7, by + 4 + i * lh), l, font=f, fill=(30, 30, 40))
    if more:                                                    # triangolino "continua"
        d.polygon([(bx + bw - 11, by + bh - 10), (bx + bw - 4, by + bh - 10),
                   (bx + bw - 7, by + bh - 6)], fill=(30, 84, 206))


# ------------------------------------------------------------------ API
def render(mood="happy", sky="day", weather=None, text="", frame=0, talking=False,
           more=False, seed=7, font_path="fonts/Silkscreen-Regular.ttf", festa=None, plane=None):
    rng = random.Random(seed)
    lo = Image.new("RGB", (LW, LH))
    d = ImageDraw.Draw(lo)
    tower = _sky(d, sky, rng)
    _celestial(d, sky)
    if weather in ("clouds", "rain"):
        _clouds(d, weather == "rain", rng)
    _city(d, tower)
    _ground(d, frame, mood == "moto")
    p = _bike(d, mood, frame, talking)
    shelter = _accessories(d, mood, frame, p)
    if weather == "rain":
        _rain(d, random.Random(seed + 1), frame, shelter)
    img = lo.resize((LW * SCALE, LH * SCALE), Image.NEAREST).crop((0, 1, W, H + 1))
    _bubble(img, text, font_path, more)
    return img
