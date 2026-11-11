"""
Alessio — il bimbo ciccioso che vive nel SmallTV, in stile sticker.

Disegno vettoriale (non pixel art): tutto e' tracciato a 4x e ridotto con
antialias, contorni blu spessi, colori pieni e bordo bianco da adesivo, come
lo sticker originale. Scena: la cameretta, con finestra sul cielo vero,
stelline e la moto giocattolo dello zio.

Interfaccia uguale a bandit.py: render(...), wrap(text, font_path), FONT.

Umori:
  happy    sorride, occhiolino ogni tanto, scintille gialle ai lati
  sleep    occhi chiusi, berretto, zZz, cameretta al buio (ciuccio solo se AGE < 4)
  rain     cappuccio giallo (fuori piove)
  moto     caschetto arancione, occhi a stellina
  tired    batteria quasi scarica che lampeggia (Claude in riserva), goccioline
  welcome  saluta con la manina, cuoricino
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 240, 200
S = 4                                    # supersampling

FONT = ("Fredoka.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/fredoka/"
        "Fredoka%5Bwdth,wght%5D.ttf")

INK = (3, 55, 100)                       # blu dello sticker
SKIN = (252, 229, 203)
SKIN_SH = (244, 208, 178)
CHEEK = (252, 179, 152)
WHITE = (255, 255, 255)
YELLOW = (250, 190, 40)
LINE = 5                                 # spessore del contorno (px a 1x)

ROOM = {
    #          muro alto          muro basso         stelline
    "day":    ((232, 242, 252), (210, 228, 248), (250, 200, 80)),
    "dawn":   ((252, 232, 220), (240, 212, 214), (250, 190, 110)),
    "sunset": ((250, 222, 204), (232, 196, 200), (250, 180, 100)),
    "rain":   ((218, 226, 236), (196, 208, 224), (230, 200, 120)),
    "night":  ((34, 42, 86),    (22, 28, 64),    (255, 230, 140)),
}
SKY = {
    "day": ((90, 165, 235), (175, 215, 250)), "dawn": ((110, 120, 190), (250, 175, 140)),
    "sunset": ((90, 70, 140), (250, 150, 90)), "rain": ((110, 120, 136), (165, 172, 184)),
    "night": ((12, 18, 46), (36, 40, 90)),
}


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Pen:
    """ImageDraw che lavora in coordinate 1x su una tela 4x."""

    def __init__(self, img):
        self.d = ImageDraw.Draw(img)

    @staticmethod
    def _b(box):
        return [v * S for v in box]

    def ellipse(self, box, fill=None, outline=None, width=0):
        self.d.ellipse(self._b(box), fill=fill, outline=outline, width=int(width * S))

    def rrect(self, box, r, fill=None, outline=None, width=0):
        self.d.rounded_rectangle(self._b(box), radius=r * S, fill=fill, outline=outline,
                                 width=int(width * S))

    def rect(self, box, fill):
        self.d.rectangle(self._b(box), fill=fill)

    def poly(self, pts, fill):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)

    def line(self, pts, fill, width=LINE):
        pts = [(x * S, y * S) for x, y in pts]
        self.d.line(pts, fill=fill, width=int(width * S), joint="curve")
        r = width * S / 2                                  # estremi arrotondati
        for x, y in (pts[0], pts[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def arc(self, box, a0, a1, fill, width=LINE):
        """Arco con estremi arrotondati."""
        self.d.arc(self._b(box), a0, a1, fill=fill, width=int(width * S))
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        rx, ry = (box[2] - box[0]) / 2 - width / 2, (box[3] - box[1]) / 2 - width / 2
        r = width * S / 2
        for a in (a0, a1):
            x = (cx + rx * math.cos(math.radians(a))) * S
            y = (cy + ry * math.sin(math.radians(a))) * S
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def chord(self, box, a0, a1, fill):
        self.d.chord(self._b(box), a0, a1, fill=fill)


# ------------------------------------------------------------------ cameretta
def _room(p, sky, weather, frame, rng, festa=None, plane=None, scene=None):
    decor = festa in ("halloween", "natale", "capodanno", "compleanno", "pasqua")
    scene = scene or {}
    top, bot, star = ROOM[sky]
    tint = SEASON_WALL.get(scene.get("stagione"))
    if tint and sky != "night":                      # il muro prende un po' del colore della stagione
        top, bot = _lerp(top, tint, .22), _lerp(bot, tint, .30)
    for y in range(H):
        p.rect([0, y, W, y + 1], _lerp(top, bot, y / H))
    # stelline a quattro punte (di notte brillano a turno)
    stars = [(214, 74, 5), (226, 104, 4), (206, 122, 3), (230, 60, 3)]
    if not decor:
        stars += [(22, 150, 4), (36, 172, 3)]
    for i, (x, y, s) in enumerate(stars):
        on = sky != "night" or (frame + i) % 3 != 0
        c = star if on else _lerp(star, bot, .6)
        p.poly([(x, y - s * 2), (x + s * .5, y - s * .5), (x + s * 2, y), (x + s * .5, y + s * .5),
                (x, y + s * 2), (x - s * .5, y + s * .5), (x - s * 2, y), (x - s * .5, y - s * .5)], c)

    # finestra ad arco con il cielo vero
    x0, y0, x1, y1 = 6, 70, 40, 128
    p.rrect([x0 - 3, y0 - 3, x1 + 3, y1 + 3], 16, fill=WHITE, outline=INK, width=2.5)
    s_top, s_bot = SKY[sky]
    win = Image.new("RGB", (W * S, H * S))
    wp = Pen(win)
    for y in range(y0, y1 + 1):
        wp.rect([x0, y, x1, y + 1], _lerp(s_top, s_bot, (y - y0) / (y1 - y0)))
    if sky == "night":
        for _ in range(7):
            sx, sy = rng.randrange(x0 + 2, x1 - 2), rng.randrange(y0 + 4, y1 - 16)
            wp.ellipse([sx - .8, sy - .8, sx + .8, sy + .8], fill=(255, 255, 230))
        wp.ellipse([x0 + 6, y0 + 8, x0 + 18, y0 + 20], fill=(250, 245, 210))
        wp.ellipse([x0 + 10, y0 + 6, x0 + 22, y0 + 18], fill=s_top)
    elif sky == "day" and weather != "rain":
        wp.ellipse([x0 + 5, y0 + 8, x0 + 19, y0 + 22], fill=(255, 210, 70))
    elif sky in ("dawn", "sunset"):
        wp.ellipse([x0 + 8, y1 - 22, x0 + 24, y1 - 6], fill=(255, 170, 90))
    tower = _lerp(s_bot, INK, .45)
    wp.rect([x0 + 21, y1 - 22, x0 + 28, y1], tower)                    # il campanile
    wp.rect([x0 + 22, y1 - 29, x0 + 27, y1 - 22], tower)
    wp.poly([(x0 + 22, y1 - 29), (x0 + 24.5, y1 - 36), (x0 + 27, y1 - 29)], tower)
    if weather in ("clouds", "rain"):
        col = (205, 210, 220) if weather == "rain" else WHITE
        wp.ellipse([x0 + 2, y0 + 14, x0 + 20, y0 + 26], fill=col)
        wp.ellipse([x0 + 10, y0 + 8, x0 + 30, y0 + 24], fill=col)
    if weather == "rain":
        for i in range(12):
            rx = x0 + 2 + (i * 11 + frame * 3) % (x1 - x0 - 4)
            ry = y0 + 24 + (i * 13 + frame * 7) % (y1 - y0 - 26)
            wp.line([(rx, ry), (rx - 1, ry + 4)], (170, 200, 240), width=1.2)
    elif weather == "snow":
        for i in range(12):
            fx = x0 + 2 + (i * 9 + frame) % (x1 - x0 - 4)
            fy = y0 + 4 + (i * 13 + frame * 2) % (y1 - y0 - 6)
            wp.ellipse([fx - 1.3, fy - 1.3, fx + 1.3, fy + 1.3], fill=WHITE)
    _season_window(wp, scene.get("stagione"), sky, weather, frame, x0, y0, x1, y1)
    if weather == "fog":                             # la nebbia copre il campanile
        for y in range(y0, y1 + 1):
            wp.rect([x0, y, x1, y + 1], _lerp(s_bot, (226, 230, 236), .55 + .35 * (y - y0) / (y1 - y0)))
    if festa:
        _festa_window(wp, festa, sky, frame, x0, y0, x1, y1)
    if plane:
        _plane_window(wp, frame, x0, y0, x1, y1)
    mask = Image.new("L", (W * S, H * S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=13 * S, fill=255)
    p.img.paste(win, (0, 0), mask)
    p.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], WHITE, width=2.5)
    p.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], WHITE, width=2.5)

    # mensola: la moto giocattolo dello zio, oppure l'oggetto del giorno (scene["oggetto"])
    p.rrect([196, 150, 240, 156], 2, fill=(205, 160, 112), outline=INK, width=2)
    if scene.get("oggetto") != "":                     # "" = niente sulla mensola (lavagnetta)
        SHELF.get(scene.get("oggetto"), _shelf_moto)(p, frame)
    # calendarietto con la data di oggi (2.0)
    if scene.get("giorno"):
        _calendar(p, scene["giorno"], scene.get("settimana", ""))


# ------------------------------------------------------------------ scene del giorno (2.0)
SEASON_WALL = {"inverno": (205, 222, 245), "primavera": (214, 240, 206),
               "estate": (255, 236, 190), "autunno": (246, 216, 186)}


def _season_window(wp, stagione, sky, weather, frame, x0, y0, x1, y1):
    """Cosa dice la stagione dalla finestra: foglie, fiori, brina, il sole d'estate."""
    if stagione == "autunno" and weather not in ("snow",):
        cols = [(225, 120, 40), (200, 80, 40), (235, 170, 50)]
        for i in range(4):
            fx = x0 + 3 + (i * 9 + frame * 2) % (x1 - x0 - 6)
            fy = y0 + 6 + (i * 17 + frame * 3) % (y1 - y0 - 10)
            wp.poly([(fx, fy - 2.5), (fx + 2.5, fy), (fx, fy + 2.5), (fx - 2.5, fy)], cols[i % 3])
    elif stagione == "primavera":
        wp.ellipse([x0 - 6, y1 - 20, x0 + 14, y1 + 2], fill=(110, 175, 90))       # una chioma verde
        for fx, fy in ((x0 + 1, y1 - 14), (x0 + 7, y1 - 8), (x0 + 10, y1 - 16)):
            wp.ellipse([fx - 1.5, fy - 1.5, fx + 1.5, fy + 1.5], fill=(250, 190, 215))
    elif stagione == "inverno" and sky != "night":
        for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):                   # brina agli angoli
            wp.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(236, 244, 252))
    elif stagione == "estate" and sky == "day" and weather is None:
        wp.ellipse([x0 + 2, y0 + 5, x0 + 22, y0 + 25], fill=(255, 232, 150))       # alone del sole
        wp.ellipse([x0 + 5, y0 + 8, x0 + 19, y0 + 22], fill=(255, 210, 70))


def _calendar(p, giorno, settimana):
    """Foglietto del calendario in alto a sinistra: giorno della settimana e numero."""
    x0, y0 = 8, 18
    p.rrect([x0, y0, x0 + 28, y0 + 32], 4, fill=WHITE, outline=INK, width=2)
    p.rrect([x0, y0, x0 + 28, y0 + 10], 4, fill=(225, 70, 60), outline=INK, width=2)
    p.rect([x0 + 1, y0 + 6, x0 + 27, y0 + 10], (225, 70, 60))
    p.cal = (x0, y0, str(giorno), settimana)           # il testo si scrive dopo la riduzione


def _calendar_text(img, p, font_path):
    cal = getattr(p, "cal", None)
    if not cal:
        return
    x0, y0, giorno, settimana = cal
    d = ImageDraw.Draw(img)
    d.text((x0 + 14, y0 + 5.5), settimana[:3].upper(), font=_nfont(font_path, 7), fill=WHITE, anchor="mm")
    d.text((x0 + 14, y0 + 21), giorno, font=_nfont(font_path, 15), fill=INK, anchor="mm")


def _shelf_moto(p, frame):
    p.ellipse([200, 136, 214, 150], fill=INK); p.ellipse([223, 136, 237, 150], fill=INK)
    p.ellipse([204, 140, 210, 146], fill=(205, 210, 220)); p.ellipse([227, 140, 233, 146], fill=(205, 210, 220))
    p.poly([(206, 138), (213, 128), (226, 127), (232, 138)], (46, 80, 170))
    p.line([(226, 128), (230, 121)], INK, width=2)
    p.ellipse([230, 129, 236, 135], fill=(255, 225, 120), outline=INK, width=1.5)


def _shelf_razzo(p, frame):
    p.poly([(218, 112), (226, 126), (226, 146), (210, 146), (210, 126)], WHITE)
    p.line([(218, 112), (226, 126), (226, 146), (210, 146), (210, 126), (218, 112)], INK, width=2)
    p.ellipse([214, 127, 222, 135], fill=(120, 190, 240), outline=INK, width=1.5)
    p.poly([(210, 136), (203, 150), (210, 146)], (225, 70, 60))
    p.poly([(226, 136), (233, 150), (226, 146)], (225, 70, 60))


def _shelf_gatto(p, frame):
    c = (245, 160, 70)
    p.ellipse([204, 128, 232, 150], fill=c, outline=INK, width=2)               # pelouche raggomitolato
    p.ellipse([222, 120, 238, 136], fill=c, outline=INK, width=2)
    p.poly([(224, 124), (225, 116), (229, 122)], c); p.poly([(232, 122), (236, 116), (237, 125)], c)
    p.arc([226, 126, 231, 131], 200, 340, INK, width=1.2); p.arc([232, 126, 237, 131], 200, 340, INK, width=1.2)
    p.arc([200, 132, 212, 150], 90, 270, INK, width=2)


def _shelf_barca(p, frame):
    p.poly([(200, 138), (236, 138), (230, 148), (206, 148)], (225, 70, 60))
    p.line([(200, 138), (236, 138), (230, 148), (206, 148), (200, 138)], INK, width=2)
    p.line([(218, 138), (218, 114)], INK, width=2)
    p.poly([(219, 116), (232, 134), (219, 134)], WHITE)
    p.poly([(217, 118), (205, 134), (217, 134)], (250, 230, 150))


def _shelf_radio(p, frame):
    p.rrect([202, 126, 236, 148], 4, fill=(190, 120, 70), outline=INK, width=2)
    p.ellipse([206, 130, 222, 146], fill=(240, 225, 200), outline=INK, width=1.5)
    p.rect([226, 131, 232, 134], INK); p.rect([226, 138, 232, 141], INK)
    p.line([(230, 126), (236, 112)], INK, width=1.5)
    if frame % 2:                                                                 # una notina che esce
        p.ellipse([205, 114, 210, 118], fill=INK); p.line([(209.5, 116), (209.5, 106)], INK, width=1.2)


def _shelf_dino(p, frame):
    c = (110, 185, 100)
    p.ellipse([206, 128, 230, 146], fill=c, outline=INK, width=2)
    p.line([(226, 132), (232, 118)], c, width=6); p.ellipse([228, 112, 240, 122], fill=c, outline=INK, width=2)
    p.poly([(206, 138), (196, 146), (208, 144)], c)
    for x in (210, 218, 224):
        p.rect([x, 144, x + 4, 150], c)
    p.ellipse([235, 115, 237, 117], fill=INK)


def _shelf_pallone(p, frame):
    p.ellipse([206, 124, 232, 150], fill=WHITE, outline=INK, width=2)
    p.poly([(219, 131), (225, 135), (223, 142), (215, 142), (213, 135)], INK)


def _shelf_globo(p, frame):
    p.ellipse([206, 118, 232, 144], fill=(110, 170, 235), outline=INK, width=2)
    p.ellipse([211, 123, 222, 134], fill=(110, 185, 100)); p.ellipse([221, 132, 229, 140], fill=(110, 185, 100))
    p.arc([202, 114, 236, 148], 100, 260, INK, width=2)
    p.rect([217, 144, 221, 148], INK); p.rrect([210, 147, 228, 150], 1, fill=INK)


def _shelf_libri(p, frame):
    for x, h, c in ((200, 26, (225, 70, 60)), (208, 30, (70, 140, 230)), (216, 24, (250, 190, 40)),
                    (224, 28, (110, 185, 100))):
        p.rrect([x, 150 - h, x + 7, 150], 1, fill=c, outline=INK, width=1.5)


def _shelf_pianta(p, frame):
    p.poly([(208, 136), (228, 136), (225, 150), (211, 150)], (200, 110, 70))
    for a, c in ((-1, (90, 160, 80)), (0, (110, 185, 100)), (1, (90, 160, 80))):
        p.ellipse([214 + a * 8, 116 + abs(a) * 4, 222 + a * 8, 136], fill=c, outline=INK, width=1.2)


SHELF = {"moto": _shelf_moto, "razzo": _shelf_razzo, "gatto": _shelf_gatto, "barca": _shelf_barca,
         "radio": _shelf_radio, "dino": _shelf_dino, "pallone": _shelf_pallone, "globo": _shelf_globo,
         "libri": _shelf_libri, "pianta": _shelf_pianta}
# interesse del carattere -> oggetto sulla mensola
OGGETTO_DI = {"spazio": "razzo", "moto": "moto", "animali": "gatto", "mare": "barca", "musica": "radio",
              "dinosauri": "dino", "sport": "pallone", "meteo": "globo", "vento": "globo", "cibo": "pianta"}


def stagione(d):
    """La stagione di una data (astronomica, arrotondata al 21)."""
    md = (d.month, d.day)
    if md >= (12, 21) or md < (3, 21):
        return "inverno"
    if md < (6, 21):
        return "primavera"
    if md < (9, 23):
        return "estate"
    return "autunno"


# ------------------------------------------------------------------ feste
ORANGE, ORANGE_DK = (245, 140, 40), (215, 100, 25)
GREEN, GREEN_DK = (90, 170, 80), (50, 120, 60)
RED, RED_DK = (225, 50, 50), (175, 30, 35)


def _bat(p, x, y, flap):
    """Pipistrellino stilizzato (flap 0/1 = ali su/giu')."""
    c = (40, 30, 60)
    p.ellipse([x - 4, y - 3, x + 4, y + 4], fill=c)
    wy = -5 if flap else 3
    p.poly([(x - 3, y), (x - 16, y + wy), (x - 12, y + 3), (x - 8, y + wy + 4), (x - 3, y + 3)], c)
    p.poly([(x + 3, y), (x + 16, y + wy), (x + 12, y + 3), (x + 8, y + wy + 4), (x + 3, y + 3)], c)
    p.poly([(x - 3, y - 2), (x - 2, y - 6), (x, y - 3)], c)
    p.poly([(x + 3, y - 2), (x + 2, y - 6), (x, y - 3)], c)


def _jack(p, x, y, lit):
    """Zucca di Halloween con faccina (accesa di notte)."""
    p.line([(x + 17, y + 2), (x + 19, y - 5)], GREEN_DK, width=4)
    for dx in (0, 10, 20):
        p.ellipse([x + dx - 2, y, x + dx + 16, y + 28], fill=ORANGE, outline=INK, width=2.5)
    p.ellipse([x + 7, y, x + 25, y + 28], fill=ORANGE)
    face = (255, 225, 90) if lit else (90, 50, 20)
    p.poly([(x + 8, y + 9), (x + 13, y + 9), (x + 10.5, y + 4)], face)
    p.poly([(x + 21, y + 9), (x + 26, y + 9), (x + 23.5, y + 4)], face)
    p.poly([(x + 7, y + 16), (x + 27, y + 16), (x + 24, y + 22), (x + 17, y + 19), (x + 10, y + 22)], face)


def _tree(p, x, y, frame):
    """Alberello di Natale con lucine che lampeggiano."""
    p.rect([x + 15, y + 40, x + 21, y + 48], (130, 85, 50))
    for w, yy in ((36, 26), (28, 14), (20, 2)):
        p.poly([(x + 18 - w / 2, y + yy + 16), (x + 18 + w / 2, y + yy + 16), (x + 18, y + yy - 4)], GREEN_DK)
    cols = [(255, 80, 80), (255, 220, 80), (120, 200, 255), (255, 140, 220)]
    for i, (lx, ly) in enumerate(((10, 38), (26, 36), (14, 26), (23, 22), (18, 12), (12, 32))):
        c = cols[(i + frame) % len(cols)]
        p.ellipse([x + lx - 2, y + ly - 2, x + lx + 2, y + ly + 2], fill=c)
    p.poly([(x + 18, y - 9), (x + 20, y - 4), (x + 25, y - 4), (x + 21, y - 1), (x + 23, y + 4),
            (x + 18, y + 1), (x + 13, y + 4), (x + 15, y - 1), (x + 11, y - 4), (x + 16, y - 4)], YELLOW)


def _balloons(p, x, y, frame):
    sway = 2 if frame % 2 else 0
    for i, (dx, c) in enumerate(((0, RED), (16, (80, 160, 240)), (8, YELLOW))):
        bx, by = x + dx + (sway if i % 2 else -sway), y + (i % 2) * 8
        p.line([(bx + 7, by + 18), (x + 14, y + 52)], INK, width=1.5)
        p.ellipse([bx, by, bx + 14, by + 18], fill=c, outline=INK, width=2)
        p.ellipse([bx + 3, by + 3, bx + 6, by + 7], fill=WHITE)


def _egg(p, x, y):
    p.ellipse([x, y, x + 26, y + 34], fill=(120, 70, 40), outline=INK, width=2.5)
    p.line([(x + 3, y + 14), (x + 23, y + 14)], (250, 200, 80), width=3)
    p.line([(x + 3, y + 20), (x + 23, y + 20)], (240, 120, 160), width=3)
    p.ellipse([x + 6, y + 4, x + 10, y + 10], fill=(160, 110, 80))


def _luminarie(p, frame):
    """Luminarie della festa patronale: archi di lucine colorate sul muro."""
    cols = [(255, 220, 90), (255, 120, 120), (130, 220, 255), (190, 140, 255)]
    for a, (x0, x1) in enumerate(((44, 120), (120, 196))):
        for i in range(9):
            t = i / 8
            x = x0 + (x1 - x0) * t
            yy = 52 + math.sin(t * math.pi) * 10
            c = cols[(i + a + frame) % len(cols)]
            p.ellipse([x - 2.5, yy - 2.5, x + 2.5, yy + 2.5], fill=c)


def _festa_room(p, festa, sky, frame):
    """Decorazioni nella cameretta (a sinistra, sotto la finestra, e nel cielo)."""
    if festa == "halloween":
        _jack(p, 6, 154, lit=sky in ("night", "sunset", "dawn"))
        for i, (bx, by) in enumerate(((210, 70), (226, 100))):
            _bat(p, bx + (frame % 3) - 1, by - (frame + i) % 2 * 3, (frame + i) % 2)
    elif festa == "natale":
        _tree(p, 4, 138, frame)
    elif festa in ("compleanno", "capodanno"):
        _balloons(p, 6, 132, frame)
    elif festa == "pasqua":
        _egg(p, 10, 150)
    elif festa == "patrono":
        _luminarie(p, frame)


def _festa_window(wp, festa, sky, frame, x0, y0, x1, y1):
    """Cosa si vede dalla finestra nei giorni di festa."""
    if festa == "halloween":
        _bat(wp, x0 + 8 + (frame * 3) % 20, y0 + 14, frame % 2)
    elif festa == "natale":
        for i in range(10):
            fx = x0 + 2 + (i * 7 + frame) % (x1 - x0 - 4)
            fy = y0 + 2 + (i * 11 + frame * 3) % (y1 - y0 - 4)
            wp.ellipse([fx - 1.2, fy - 1.2, fx + 1.2, fy + 1.2], fill=WHITE)
    elif festa == "capodanno" and sky in ("night", "sunset"):
        cols = [(255, 120, 120), (255, 230, 120), (140, 220, 255)]
        for i, (cx, cy) in enumerate(((x0 + 10, y0 + 14), (x0 + 24, y0 + 26))):
            r = 4 + ((frame + i) % 3) * 3
            for k in range(8):
                a = math.radians(k * 45)
                wp.line([(cx + math.cos(a) * r * .4, cy + math.sin(a) * r * .4),
                         (cx + math.cos(a) * r, cy + math.sin(a) * r)], cols[(i + k) % 3], width=1.2)


def _plane_window(wp, frame, x0, y0, x1, y1):
    """Un aereo che attraversa la finestra (contorno blu, cosi' si vede bene)."""
    px = x0 + 6 + (frame * 3) % (x1 - x0 - 10)
    py = y0 + 20
    for c, g in ((INK, 1.6), ((252, 252, 255), 0)):
        wp.poly([(px - 11 - g, py - 1 - g), (px + 9, py - 2 - g), (px + 13 + g, py + 1),
                 (px + 9, py + 3 + g), (px - 11 - g, py + 3 + g)], c)              # fusoliera
        wp.poly([(px - 2 - g, py), (px + 4 + g, py), (px - 5 - g, py + 10 + g)], c)  # ala
        wp.poly([(px - 2 - g, py), (px + 4 + g, py), (px - 5 - g, py - 8 - g)], c)   # ala sopra
        wp.poly([(px - 11 - g, py), (px - 6 + g, py), (px - 12 - g, py - 6 - g)], c)  # coda
    for k in range(1, 4):                                                          # scia
        wp.line([(px - 13 - k * 5, py + 1), (px - 10 - k * 5, py + 1)], WHITE, width=1.5)


def _blanket(p):
    p.rrect([-10, 186, W + 10, H + 20], 10, fill=(160, 205, 245), outline=INK, width=LINE)
    for x in range(8, W, 18):
        p.ellipse([x - 2, 194, x + 2, 198], fill=WHITE)


# ------------------------------------------------------------------ Alessio
CX = 120


HAIR, HAIR_HI = (150, 104, 62), (198, 152, 98)       # castano chiaro, con riflessi biondi
SHIRT, SHIRT_DK = (92, 62, 168), (64, 40, 128)        # maglia viola da squadra
TRIM = (255, 255, 255)


def _older():
    """Da 8 anni in su (2.0): viso piu' lungo, capelli veri, maglietta. Sotto, il bimbo dello sticker."""
    return AGE >= 8


def _head_shape(p, fill, g=0, y=0):
    """Testa: da piccolo calotta + guanciotte piene; da ragazzino un ovale con il mento."""
    if _older():
        p.ellipse([CX - 64 - g, 34 + y - g, CX + 64 + g, 172 + y + g], fill=fill)
        p.ellipse([CX - 66 - g, 94 + y - g, CX + 64 + g, 194 + y + g], fill=fill)   # guance piene
        return
    p.ellipse([CX - 64 - g, 40 + y - g, CX + 64 + g, 168 + y + g], fill=fill)
    p.ellipse([CX - 72 - g, 92 + y - g, CX + 70 + g, 196 + y + g], fill=fill)


def _shirt(p, y):
    """Spalle e maglia da squadra (da ragazzino): viola, bordo bianco al collo e righe sulle spalle."""
    p.rrect([CX - 90, 174 + y, CX + 90, 240 + y], 36, fill=SHIRT, outline=INK, width=LINE)
    for side in (-1, 1):                                             # righe bianche sulle spalle
        p.arc([CX + side * 70 - 26, 178 + y, CX + side * 70 + 26, 230 + y],
              200 if side < 0 else 250, 290 if side < 0 else 340, TRIM, width=5)
    p.rrect([CX - 24, 170 + y, CX + 22, 196 + y], 10, fill=SKIN, outline=INK, width=LINE)   # collo
    p.arc([CX - 32, 164 + y, CX + 30, 208 + y], 15, 165, TRIM, width=7)                   # colletto bianco
    p.arc([CX - 32, 164 + y, CX + 30, 208 + y], 15, 165, INK, width=2)


def _hair(p, y, ciuffo=True):
    """Capelli da ragazzino: castano chiaro, folti sopra, frangia lunga pettinata di lato che
    scende in diagonale sulla fronte (da sinistra in alto a destra in basso), basette corte."""
    p.chord([CX - 68, 20 + y, CX + 68, 132 + y], 180, 360, fill=INK)
    p.chord([CX - 63, 25 + y, CX + 63, 127 + y], 180, 360, fill=HAIR)
    for side in (-1, 1):                                             # basette
        x = CX + side * 57
        p.poly([(x - 9, 70 + y), (x + 9, 70 + y), (x + side * 3, 104 + y)], INK)
        p.poly([(x - 6, 72 + y), (x + 6, 72 + y), (x + side * 3, 98 + y)], HAIR)
    # frangia: un'unica ciocca larga che scende verso destra, con le punte
    edge = [(CX - 62, 70), (CX - 50, 80), (CX - 38, 76), (CX - 22, 88), (CX - 8, 84), (CX + 10, 96),
            (CX + 24, 92), (CX + 40, 102), (CX + 52, 92), (CX + 62, 98), (CX + 62, 66)]
    p.poly([(x, yy - 6 + y) for x, yy in [(CX - 62, 56)] + edge[:-1]] + [(CX + 64, 66 + y)], HAIR)
    p.line([(x, yy + y) for x, yy in edge[:-1]], INK, width=3.5)
    p.poly([(CX - 62, 56 + y)] + [(x, yy - 3 + y) for x, yy in edge[:-1]]
           + [(CX + 63, 62 + y), (CX + 60, 50 + y)], HAIR)
    for x0, y0, x1, y1 in ((CX - 30, 46, CX - 4, 78), (CX + 2, 50, CX + 30, 86)):   # ciocche
        p.line([(x0, y0 + y), (x1, y1 + y)], _lerp(HAIR, INK, .35), width=2.5)
    p.arc([CX - 50, 30 + y, CX + 26, 92 + y], 200, 262, HAIR_HI, width=5)           # riflesso
    if ciuffo:                                                                      # ciuffetto
        p.line([(CX - 6, 26 + y), (CX + 4, 12 + y)], INK, width=7)
        p.line([(CX - 6, 26 + y), (CX + 4, 12 + y)], HAIR, width=3)


def _ears(p, y):
    if _older():
        for ex in (CX - 68, CX + 66):
            left = ex < CX
            p.ellipse([ex - 12, 110 + y, ex + 12, 136 + y], fill=SKIN, outline=INK, width=LINE)
            p.arc([ex - 5, 116 + y, ex + 5, 130 + y], 100 if left else -80, 260 if left else 80,
                  INK, width=2.5)
        return
    for ex, sgn in ((CX - 72, -1), (CX + 70, 1)):
        p.ellipse([ex - 15, 104 + y, ex + 15, 136 + y], fill=SKIN, outline=INK, width=LINE)
        a0, a1 = (100, 260) if sgn < 0 else (-80, 80)
        p.arc([ex - 7, 112 + y, ex + 7, 128 + y], a0, a1, INK, width=3)


def _character(mood, frame, talking, y, festa=None, plane=None):
    """Livello RGBA con Alessio, gia' a 4x."""
    layer = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    p = Pen(layer)
    older = _older()
    if older:
        _shirt(p, y)
    _ears(p, y)
    _head_shape(p, INK, g=LINE, y=y)
    _head_shape(p, SKIN, y=y)
    if not older:
        p.arc([CX - 50, 58 + y, CX + 10, 130 + y], 200, 245, WHITE, width=3.5)    # luce sulla fronte

    hat = festa if (festa in HATS and mood != "sleep") else None
    # i capelli solo dove non c'e' niente in testa: berretto, casco, zucca e Babbo Natale li coprono
    # tutti; il cappellino a cono e le orecchie di Pasqua stanno sopra ai capelli
    if older and mood not in ("moto", "sleep") and hat not in ("halloween", "natale"):
        _hair(p, y, ciuffo=not hat)
    # ciuffo: tre ciocche che partono dalla testa e si arricciano, come lo sticker (da piccolo)
    if not older and mood not in ("rain", "moto", "sleep") and not hat:
        for (x0, y0), (xc, yc), (x1, y1), wdt in (
                ((CX - 8, 44), (CX - 14, 26), (CX - 26, 20), LINE),
                ((CX - 1, 42), (CX - 2, 18), (CX + 10, 12), LINE),
                ((CX + 6, 44), (CX + 14, 28), (CX + 26, 26), 4)):
            pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * xc + t * t * x1,
                    (1 - t) ** 2 * y0 + 2 * (1 - t) * t * yc + t * t * y1 + y) for t in
                   [i / 12 for i in range(13)]]
            p.line(pts, INK, width=wdt)
        p.arc([CX + 6, 8 + y, CX + 18, 20 + y], 180, 420, INK, width=3.5)    # ricciolo

    # occhi
    ex1, ex2, ey = CX - 30, CX + 26, 120 + y
    look = 0 if talking else (2 if frame % 40 < 6 else 0) - (2 if 20 <= frame % 40 < 26 else 0)
    up = 0
    if plane and mood != "sleep":                                  # guarda l'aereo alla finestra
        look, up = -4, -4
    blink = frame % 11 == 10
    wink = mood in ("happy", "welcome") and frame % 23 in (11, 12)
    for k, ex in enumerate((ex1, ex2)):
        if mood == "sleep" or blink:
            p.arc([ex - 9, ey - 6, ex + 9, ey + 8], 20, 160, INK, width=LINE)
        elif wink and k == 1:
            p.arc([ex - 9, ey - 2, ex + 9, ey + 14], 200, 340, INK, width=LINE)
        elif mood == "tired":
            p.ellipse([ex - 7, ey - 2, ex + 7, ey + 12], fill=INK)
            p.rect([ex - 8, ey - 4, ex + 8, ey + 4], SKIN)
            p.line([(ex - 9, ey + 3), (ex + 9, ey + 3)], INK, width=3.5)
        else:
            r = 6.5 if older else 8
            p.ellipse([ex - r + look, ey - r - 2 + up, ex + r + look, ey + r + 2 + up], fill=INK)
            p.ellipse([ex - 4 + look, ey - 6 + up, ex + 0 + look, ey - 2 + up], fill=WHITE)
            if mood == "moto":
                p.ellipse([ex + 2 + look, ey + 2, ex + 5 + look, ey + 5], fill=WHITE)
    if older and mood not in ("sleep", "rain", "moto"):            # sopracciglia
        tilt = 3 if mood == "tired" else 0
        p.line([(ex1 - 11, ey - 17 + tilt), (ex1 + 9, ey - 20)], INK, width=4)
        p.line([(ex2 - 9, ey - 21), (ex2 + 11, ey - 17 + tilt)], INK, width=4)
    elif mood not in ("sleep", "tired", "rain", "moto"):          # sopracciglio furbetto
        p.arc([ex2 - 10, ey - 26, ex2 + 10, ey - 8], 210, 330, INK, width=3.5)

    # guance (da piccolo guanciotte piene)
    if older:
        p.ellipse([CX - 60, 134 + y, CX - 36, 154 + y], fill=_lerp(SKIN, CHEEK, .7))
        p.ellipse([CX + 32, 132 + y, CX + 56, 152 + y], fill=_lerp(SKIN, CHEEK, .7))
    else:
        p.ellipse([CX - 66, 132 + y, CX - 38, 158 + y], fill=CHEEK)
        p.ellipse([CX + 36, 130 + y, CX + 64, 156 + y], fill=CHEEK)

    # bocca
    mx, my = CX - 2, 150 + y
    if mood == "sleep" and AGE < 4:                                # ciuccio (solo da piccolo)
        p.ellipse([mx - 13, my - 6, mx + 13, my + 14], fill=(120, 190, 240), outline=INK, width=3)
        p.ellipse([mx - 5, my, mx + 5, my + 8], fill=(230, 245, 255), outline=INK, width=2)
    elif mood == "sleep":                                          # dorme con la bocca chiusa
        p.arc([mx - 9, my, mx + 9, my + 10], 20, 160, INK, width=3)
    elif plane and not talking:                                    # "ooh!"
        p.ellipse([mx - 7, my - 2, mx + 7, my + 14], fill=INK)
        p.ellipse([mx - 4, my + 6, mx + 4, my + 12], fill=CHEEK)
    elif talking and frame % 2 == 0:
        p.ellipse([mx - 9, my - 4, mx + 9, my + 14], fill=INK)
        p.ellipse([mx - 6, my + 5, mx + 6, my + 13], fill=CHEEK)
    elif mood == "tired":
        p.arc([mx - 10, my + 2, mx + 10, my + 16], 200, 340, INK, width=4)
    elif older:                                                    # sorriso largo, con i denti
        p.chord([mx - 20, my - 16, mx + 20, my + 12], 0, 180, fill=INK)
        p.chord([mx - 16, my - 13, mx + 16, my + 8], 0, 180, fill=WHITE)
        p.line([(mx - 16, my - 1), (mx + 16, my - 1)], INK, width=2.5)
        p.arc([mx - 26, my - 14, mx - 16, my - 2], 120, 220, INK, width=2.5)       # fossette
        p.arc([mx + 16, my - 14, mx + 26, my - 2], 320, 420, INK, width=2.5)
    else:                                                          # sorriso storto, come lo sticker
        p.arc([mx - 16, my - 18, mx + 18, my + 6], 30, 140, INK, width=LINE)
        p.arc([mx + 12, my - 6, mx + 22, my + 2], 300, 400, INK, width=3.5)  # fossetta

    if hat:
        _hat(p, hat, frame, y)
        if mood not in ("rain", "moto"):
            _accessories(p, mood, frame, y)
    else:
        _accessories(p, mood, frame, y)

    # manine che spuntano
    def mitt(x, yy, wave=False):
        p.rrect([x, yy, x + 40, yy + 46], 18, fill=SKIN, outline=INK, width=LINE)
        if not wave:
            for fx in (x + 14, x + 26):
                p.line([(fx, yy + 2), (fx, yy + 12)], INK, width=3.5)
        else:
            for fx in (x + 10, x + 20, x + 30):
                p.line([(fx, yy + 2), (fx, yy + 9)], INK, width=3)
    if not older:                                # da ragazzino niente manine sul mento: si vede la maglia
        mitt(CX - 64, 168)
    if mood == "welcome":
        k = frame % 2
        hx, hy = (CX + 48 + k * 3, 100 - k * 5) if older else (CX + 62 + k * 3, 92 - k * 5)
        p.line([(CX + 40, 196), (hx + 16, hy + 30)], INK, width=LINE + 18)
        p.line([(CX + 40, 196), (hx + 16, hy + 30)], SKIN, width=18)
        mitt(hx, hy, wave=True)
        for i in range(0 if older else 3):                         # trattini del saluto (solo da piccolo)
            a = math.radians(-40 + i * 40)
            p.line([(hx + 44 + 4 * math.cos(a), hy + 20 + 10 * math.sin(a)),
                    (hx + 50 + 7 * math.cos(a), hy + 20 + 14 * math.sin(a))], INK, width=3)
    elif not older:
        mitt(CX + 22, 168)
    return layer


HATS = ("halloween", "natale", "capodanno", "compleanno", "pasqua")


def _hat(p, festa, frame, y):
    """Cappelli delle feste (sostituiscono ciuffo, cappuccio e casco; non il berretto da notte)."""
    if festa == "halloween":                                   # cappuccio a zucca
        p.chord([CX - 70, 24 + y, CX + 70, 140 + y], 180, 360, fill=INK)
        p.chord([CX - 65, 29 + y, CX + 65, 135 + y], 180, 360, fill=ORANGE)
        for dx in (-34, 0, 34):                                # spicchi
            p.arc([CX + dx - 22, 30 + y, CX + dx + 22, 150 + y], 200, 340, ORANGE_DK, width=3)
        p.rrect([CX - 72, 76 + y, CX + 72, 90 + y], 7, fill=ORANGE_DK, outline=INK, width=4)
        p.rrect([CX - 6, 10 + y, CX + 6, 32 + y], 4, fill=GREEN_DK, outline=INK, width=3)  # picciolo
        p.ellipse([CX + 4, 10 + y, CX + 26, 22 + y], fill=GREEN, outline=INK, width=2.5)    # foglia
        p.arc([CX - 46, 40 + y, CX + 6, 84 + y], 200, 250, (255, 200, 140), width=4)
    elif festa == "natale":                                    # cappello di Babbo Natale
        p.poly([(CX - 62, 84 + y), (CX + 64, 84 + y), (CX + 50, 46 + y), (CX + 92, 62 + y),
                (CX + 74, 30 + y), (CX + 10, 12 + y), (CX - 40, 34 + y)], INK)
        p.poly([(CX - 56, 80 + y), (CX + 58, 80 + y), (CX + 46, 42 + y), (CX + 84, 56 + y),
                (CX + 68, 34 + y), (CX + 10, 18 + y), (CX - 36, 38 + y)], RED)
        p.arc([CX - 30, 24 + y, CX + 40, 80 + y], 200, 250, (255, 140, 140), width=4)
        p.rrect([CX - 68, 72 + y, CX + 68, 92 + y], 10, fill=WHITE, outline=INK, width=4)
        p.ellipse([CX + 80, 44 + y, CX + 102, 66 + y], fill=WHITE, outline=INK, width=4)
    elif festa in ("capodanno", "compleanno"):                 # cappellino a cono
        cols = [(80, 160, 240), YELLOW, (240, 90, 140)]
        p.poly([(CX - 36, 62 + y), (CX + 20, 50 + y), (CX - 14, -2 + y)], INK)
        p.poly([(CX - 31, 58 + y), (CX + 15, 48 + y), (CX - 14, 6 + y)], cols[0])
        for i, t in enumerate((0.35, 0.65)):                   # righe
            a = (CX - 14 + (-17) * t, 6 + 52 * t + y); b = (CX - 14 + 29 * t, 6 + 42 * t + y)
            p.line([a, b], cols[1 + i], width=4)
        p.ellipse([CX - 22, -10 + y, CX - 6, 6 + y], fill=cols[2], outline=INK, width=3)
        if festa == "capodanno" or frame % 2:                  # coriandoli
            for i, (cx, cy) in enumerate(((CX - 70, 40), (CX + 60, 30), (CX - 50, 10), (CX + 40, 60))):
                c = cols[(i + frame) % 3]
                p.rect([cx, cy + (frame % 2) * 3, cx + 5, cy + 5 + (frame % 2) * 3], c)
    elif festa == "pasqua":                                     # orecchie da coniglio
        for dx, tilt in ((-30, -10), (18, 10)):
            p.ellipse([CX + dx - 13 + tilt, -6 + y, CX + dx + 13 + tilt, 66 + y], fill=WHITE,
                      outline=INK, width=4)
            p.ellipse([CX + dx - 6 + tilt, 6 + y, CX + dx + 6 + tilt, 56 + y], fill=(250, 180, 200))
        p.rrect([CX - 56, 48 + y, CX + 56, 60 + y], 6, fill=(250, 180, 200), outline=INK, width=3)


def _accessories(p, mood, frame, y):
    if mood == "sleep":
        cap, band = (90, 110, 215), WHITE
        p.chord([CX - 66, 32 + y, CX + 66, 136 + y], 180, 360, fill=INK)
        p.chord([CX - 61, 37 + y, CX + 61, 131 + y], 180, 360, fill=cap)
        p.poly([(CX - 20, 38 + y), (CX + 58, 62 + y), (CX + 86, 96 + y), (CX + 40, 70 + y)], cap)
        p.rrect([CX - 68, 78 + y, CX + 68, 94 + y], 8, fill=band, outline=INK, width=4)
        p.ellipse([CX + 76, 88 + y, CX + 96, 108 + y], fill=band, outline=INK, width=4)
    elif mood == "rain" and _older():
        pass                                     # da ragazzino niente cappuccio: si vede la pioggia alla finestra
    elif mood == "rain":
        hood, hood_dk = (250, 205, 40), (215, 160, 20)
        p.chord([CX - 76, 28 + y, CX + 76, 148 + y], 180, 360, fill=INK)
        p.chord([CX - 71, 33 + y, CX + 71, 143 + y], 180, 360, fill=hood)
        p.rrect([CX - 78, 80 + y, CX + 78, 94 + y], 7, fill=hood_dk, outline=INK, width=4)
        p.arc([CX - 50, 44 + y, CX + 10, 90 + y], 200, 250, (255, 240, 160), width=4)
    elif mood == "moto":
        helm = (245, 120, 30)
        p.chord([CX - 70, 26 + y, CX + 70, 140 + y], 180, 360, fill=INK)
        p.chord([CX - 65, 31 + y, CX + 65, 135 + y], 180, 360, fill=helm)
        p.rect([CX - 8, 31 + y, CX + 8, 80 + y], WHITE)
        p.rrect([CX - 72, 76 + y, CX + 72, 90 + y], 7, fill=(40, 46, 70), outline=INK, width=4)
        p.arc([CX - 46, 40 + y, CX + 6, 84 + y], 200, 250, (255, 200, 140), width=4)
        for i, yy in enumerate(() if _older() else (70, 100, 130)):   # da grande finivano sulla mensola
            ln = 10 + ((frame + i) % 3) * 6
            p.line([(W - 6 - ln, yy), (W - 6, yy)], INK, width=3)
    elif mood == "tired":
        bx, by = 174, 88                                           # batteria quasi scarica (accanto a lui)
        p.rrect([bx + 7, by + 2, bx + 15, by + 9], 2, fill=(200, 205, 215), outline=INK, width=2.5)
        p.rrect([bx + 1, by + 8, bx + 21, by + 50], 5, fill=WHITE, outline=INK, width=3)
        lvl = (240, 70, 60) if frame % 2 == 0 else (250, 230, 230)
        p.rect([bx + 4, by + 41, bx + 18, by + 47], lvl)
        for dx, dy in ((0, 0), (10, 16)):                          # goccioline di sudore
            sx, sy = CX - (74 if _older() else 82) - dx, 70 + dy + (frame % 3) * 2
            p.poly([(sx, sy), (sx - 4, sy + 7), (sx + 4, sy + 7)], (120, 180, 250))
            p.ellipse([sx - 4, sy + 3, sx + 4, sy + 11], fill=(120, 180, 250))
    elif mood == "welcome" and not _older():
        hx, hy = CX - 104, 56 - (frame % 3) * 2
        p.ellipse([hx, hy, hx + 14, hy + 13], fill=(240, 70, 110))
        p.ellipse([hx + 11, hy, hx + 25, hy + 13], fill=(240, 70, 110))
        p.poly([(hx + 1, hy + 9), (hx + 24, hy + 9), (hx + 12.5, hy + 24)], (240, 70, 110))


def _zzz(img, frame):
    """zZz che salgono, disegnate sopra a tutto (senza bordo bianco)."""
    big = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    p = Pen(big)
    zc = (225, 232, 255)
    for i, (zx, zy, sz) in enumerate(((176, 74, 7), (188, 54, 9), (202, 30, 11))):
        if i <= frame % 4:
            p.line([(zx, zy), (zx + sz, zy)], zc, width=2.2)
            p.line([(zx + sz, zy), (zx, zy + sz)], zc, width=2.2)
            p.line([(zx, zy + sz), (zx + sz, zy + sz)], zc, width=2.2)
    small = big.resize((W, H), Image.LANCZOS)
    img.paste(small, (0, 0), small)


def _sparks(p, mood, frame):
    """Le scintille gialle ai lati, come nello sticker (solo da piccolo: da grande finivano sui
    capelli e sul calendario)."""
    if mood not in ("happy", "welcome", "moto") or _older():
        return
    grow = 2 if frame % 2 else 0
    for side in (-1, 1):
        bx, by = CX + side * 66, 70
        for a in (-70, -35, 0):
            ang = math.radians(a if side > 0 else 180 - a)
            r0, r1 = 10, 22 + grow
            p.line([(bx + r0 * math.cos(ang), by + r0 * math.sin(ang)),
                    (bx + r1 * math.cos(ang), by + r1 * math.sin(ang))], YELLOW, width=5)


# ------------------------------------------------------------------ nuvoletta
_FONT_CACHE = {}
BUBBLE_W = 206
BUBBLE_LINES = 3
FONT_PX = 17
LINE_H = 19


def _font(path):
    if path not in _FONT_CACHE:
        f = ImageFont.truetype(path, FONT_PX)
        try:
            f.set_variation_by_name("SemiBold")
        except Exception:
            pass
        _FONT_CACHE[path] = f
    return _FONT_CACHE[path]


def wrap(text, font_path):
    f = _font(font_path)
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
    f = _font(font_path)
    d = ImageDraw.Draw(img)
    lines = page.split("\n")
    bw = int(max(d.textlength(l, font=f) for l in lines)) + 22 + (10 if more else 0)
    bh = len(lines) * LINE_H + 12
    bx, by = max(4, 236 - bw), 4
    # disegno a 4x per bordi morbidi
    big = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    p = Pen(big)
    tx = min(bx + bw - 30, 150)
    p.poly([(tx - 1, by + bh - 4), (tx + 15, by + bh - 4), (tx + 2, by + bh + 14)], INK)
    p.rrect([bx, by, bx + bw, by + bh], 12, fill=WHITE, outline=INK, width=3)
    p.poly([(tx + 2.5, by + bh - 3), (tx + 11, by + bh - 3), (tx + 3.5, by + bh + 8)], WHITE)
    if more:
        p.poly([(bx + bw - 15, by + bh - 13), (bx + bw - 6, by + bh - 13),
                (bx + bw - 10.5, by + bh - 7)], (40, 110, 210))
    small = big.resize((W, H), Image.LANCZOS)
    img.paste(small, (0, 0), small)
    for i, l in enumerate(lines):
        d.text((bx + 11, by + 5 + i * LINE_H), l, font=f, fill=INK)


# ------------------------------------------------------------------ API
AGE = 10         # anni di Alessio: lo aggiorna l'app (sotto i 4 anni dorme col ciuccio)


def render(mood="happy", sky="day", weather=None, text="", frame=0, talking=False,
           more=False, seed=7, font_path="Fredoka.ttf", festa=None, plane=None, scene=None):
    """festa: halloween | natale | capodanno | compleanno | pasqua | patrono | None
       plane: True quando un aereo passa sopra casa (lo si vede alla finestra).
       scene: (2.0) la scena del giorno, {stagione, oggetto, giorno, settimana}; weather puo'
       essere anche "fog" o "snow"."""
    rng = random.Random(seed)
    bg = Image.new("RGB", (W * S, H * S))
    p = Pen(bg)
    p.img = bg
    if text and scene:                                 # la nuvoletta coprirebbe il calendario
        scene = {k: v for k, v in scene.items() if k != "giorno"}
    _room(p, sky, weather, frame, rng, festa, plane, scene)
    if festa:
        _festa_room(p, festa, sky, frame)
    if not text:
        _sparks(p, mood, frame)
    _blanket(p)
    bg = bg.resize((W, H), Image.LANCZOS)
    _calendar_text(bg, p, font_path)

    y = 0          # niente saltello: ridisegnerebbe tutto il faccione a ogni frame
    k = 0.84                                       # Alessio un po' piu' piccolo: si vede la cameretta
    cw, chh = round(W * k), round(H * k)
    ch = _character(mood, frame, talking, y, festa, plane).resize((cw, chh), Image.LANCZOS)
    full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    full.paste(ch, ((W - cw) // 2, H - chh + 4))
    ch = full
    # bordo bianco da adesivo
    alpha = ch.getchannel("A").point(lambda a: 255 if a > 40 else 0)
    border = alpha.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(.6))
    bg.paste(WHITE, (0, 0), border)
    bg.paste(ch, (0, 0), ch)
    if mood == "sleep":
        _zzz(bg, frame)
    _bubble(bg, text, font_path, more)
    return bg


# ------------------------------------------------------------------ lavagnetta
def render_photo(photo, sky="day", weather=None, frame=0, festa=None):
    """Una foto nella lavagnetta grande: la stessa cornice bianca con i bordi stondati della
    lavagnetta, quasi a tutto schermo, sulla cameretta. Alessio non c'e': c'e' solo la foto."""
    rng = random.Random(7)
    bg = Image.new("RGB", (W * S, H * S))
    p = Pen(bg)
    p.img = bg
    _room(p, sky, weather, frame, rng, festa, None)
    cx0, cy0 = (W - photo.width) // 2, (H - photo.height) // 2
    p.rrect([cx0 - 4, cy0 - 4, cx0 + photo.width + 4, cy0 + photo.height + 4], 10,
            fill=WHITE, outline=INK, width=3)
    bg = bg.resize((W, H), Image.LANCZOS)
    mask = Image.new("L", photo.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, photo.width - 1, photo.height - 1], radius=7, fill=255)
    bg.paste(photo, (cx0, cy0), mask)
    return bg


def render_card(card, mood="happy", sky="day", weather=None, text="", frame=0, talking=False,
                more=False, seed=7, font_path="Fredoka.ttf", festa=None):
    """Alessio piccolo in basso a destra che mostra una lavagnetta (grafico o disegno).
       card: immagine RGB 196x128 (vedi grafici.py)."""
    rng = random.Random(seed)
    bg = Image.new("RGB", (W * S, H * S))
    p = Pen(bg)
    p.img = bg
    _room(p, sky, weather, frame, rng, festa, None, {"oggetto": ""})   # mensola vuota: c'e' Alessio
    _blanket(p)
    # cornice della lavagnetta
    cx0, cy0 = 6, 58
    cw_, ch_ = card.size
    p.rrect([cx0 - 4, cy0 - 4, cx0 + cw_ + 4, cy0 + ch_ + 4], 10, fill=WHITE, outline=INK, width=3)
    bg = bg.resize((W, H), Image.LANCZOS)
    mask = Image.new("L", card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw_ - 1, ch_ - 1], radius=7, fill=255)
    bg.paste(card, (cx0, cy0), mask)

    # Alessio piccolo che sbuca in basso a destra
    k = 0.36 if _older() else 0.42               # da grande la testa e' piu' larga: non copre il grafico
    cw, chh = round(W * k), round(H * k)
    hat_festa = festa if festa in HATS else None
    chl = _character(mood, frame, talking, 0, hat_festa, None).resize((cw, chh), Image.LANCZOS)
    full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    full.paste(chl, (W - cw + (14 if _older() else 8), H - chh + 6))
    alpha = full.getchannel("A").point(lambda a: 255 if a > 40 else 0)
    border = alpha.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(.5))
    bg.paste(WHITE, (0, 0), border)
    bg.paste(full, (0, 0), full)
    _bubble(bg, text, font_path, more)
    return bg


# ------------------------------------------------------------------ notte (1.8)
NOTTE_BG = (6, 10, 26)
NOTTE_INK = (118, 138, 190)
NOTTE_DIM = (72, 86, 128)
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
        "settembre", "ottobre", "novembre", "dicembre"]


def render_night(now, font_path="Fredoka.ttf", seed=7):
    """Il quadrante della notte: ora grande e tonda, data in italiano, luna, qualche stella e
    Alessio che dorme in un angolo. Colori scuri e bassi: non deve illuminare la stanza.
    Cambia solo una volta al minuto (le stelle che brillano cambiano con il minuto)."""
    img = Image.new("RGB", (W * S, H * S), NOTTE_BG)
    d = ImageDraw.Draw(img)
    # cielo: un velo appena piu' chiaro in basso
    for y in range(H * S):
        t = y / (H * S)
        d.line([(0, y), (W * S, y)], fill=(6 + int(8 * t), 10 + int(10 * t), 26 + int(16 * t)))
    # stelle: sempre le stesse posizioni, due brillano di piu' (cambiano ogni minuto)
    rng = random.Random(seed)
    stars = [(rng.randint(8, W - 8), rng.randint(6, 52)) for _ in range(14)]
    bright = random.Random(now.hour * 60 + now.minute).sample(range(len(stars)), 2)
    for i, (x, y) in enumerate(stars):
        if 178 < x < 236 and y < 44:
            continue                                            # lo spazio della luna
        if i in bright:
            r = 2.2
            d.line([((x - 4) * S, y * S), ((x + 4) * S, y * S)], fill=NOTTE_DIM, width=S)
            d.line([(x * S, (y - 4) * S), (x * S, (y + 4) * S)], fill=NOTTE_DIM, width=S)
        else:
            r = 1.1
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=NOTTE_INK if i in bright else NOTTE_DIM)
    # luna
    d.ellipse([200 * S, 10 * S, 224 * S, 34 * S], fill=(168, 160, 112))
    d.ellipse([207 * S, 6 * S, 231 * S, 30 * S], fill=(8, 12, 30))
    # ora
    f = _nfont(font_path, 76 * S)
    t = f"{now.hour:02d}:{now.minute:02d}"
    w = d.textlength(t, font=f)
    d.text(((W * S - w) / 2, 40 * S), t, font=f, fill=NOTTE_INK)
    # data
    f2 = _nfont(font_path, 15 * S)
    data = f"{GIORNI[now.weekday()]} {now.day} {MESI[now.month - 1]}"
    w2 = d.textlength(data, font=f2)
    d.text(((W * S - w2) / 2, 132 * S), data, font=f2, fill=NOTTE_DIM)
    img = img.resize((W, H), Image.LANCZOS)
    # Alessio che dorme, piccolo, in basso a sinistra (scurito come tutto il resto)
    k = 0.30
    cw, ch = round(W * k), round(H * k)
    al = _character("sleep", 0, False, 0, None, None).resize((cw, ch), Image.LANCZOS)
    rgb = Image.blend(Image.new("RGB", al.size, NOTTE_BG), al.convert("RGB"), 0.55)
    img.paste(rgb, (2, H - ch + 4), al.getchannel("A"))
    # "zzz" accanto alla testa
    dz = ImageDraw.Draw(img)
    for dx, dy, sz in ((cw - 2, H - 34, 10), (cw + 7, H - 44, 13), (cw + 18, H - 56, 16)):
        dz.text((dx, dy), "z", font=_nfont(font_path, sz), fill=NOTTE_DIM)
    return img


def _nfont(path, size):
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_name("SemiBold")
    except Exception:
        pass
    return f
