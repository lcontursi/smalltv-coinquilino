"""
Grafici e disegni che Alessio mostra sulla sua lavagnetta.

Tutte le funzioni restituiscono un'immagine RGB di CARD_W x CARD_H, disegnata a 4x
e ridotta con antialias, nello stesso stile dello sticker (contorni blu, colori pieni).

  temperature(ore, temp, pioggia, font)   prossime ore: linea delle temperature + barre pioggia
  claude(sessione, settimana, font)       due barre dei consumi
  radar(aerei, font)                      aerei intorno a casa (puntini, il piu' vicino evidenziato)
  pixel_art(righe, palette)               disegno di Claude: griglia di caratteri -> colori
  settimana(giorni, oggi, font)           (2.0) i giorni prima e dopo oggi: min/max e cielo
  icona(d, cielo, cx, cy, r)              (2.0) sole, nuvole, pioggia, neve, temporale, nebbia
"""
import math

from PIL import Image, ImageDraw, ImageFont

CARD_W, CARD_H = 162, 128
S = 4
INK = (3, 55, 100)
WHITE = (255, 255, 255)
PAPER = (255, 252, 244)
GRID = (226, 232, 242)
RED = (232, 80, 70)
BLUE = (70, 140, 230)
YELLOW = (250, 190, 40)
GREEN = (90, 170, 80)

_FONTS = {}


def _font(path, px):
    k = (path, px)
    if k not in _FONTS:
        f = ImageFont.truetype(path, px * S)
        try:
            f.set_variation_by_name("SemiBold")
        except Exception:
            pass
        _FONTS[k] = f
    return _FONTS[k]


def _canvas(w=CARD_W, h=CARD_H, bg=PAPER):
    img = Image.new("RGB", (w * S, h * S), bg)
    return img, ImageDraw.Draw(img)


def _done(img):
    return img.resize((img.width // S, img.height // S), Image.LANCZOS)


def temperature(ore, temp, pioggia, font):
    """ore: ['14', '15', ...]; temp: gradi; pioggia: probabilita' % (stessa lunghezza)."""
    img, d = _canvas()
    n = len(temp)
    if n < 2:
        return _done(img)
    x0, x1, y0, y1 = 22, CARD_W - 8, 10, CARD_H - 22
    tmin, tmax = math.floor(min(temp)) - 1, math.ceil(max(temp)) + 1
    def X(i): return (x0 + (x1 - x0) * i / (n - 1)) * S
    def Y(t): return (y1 - (y1 - y0) * (t - tmin) / max(1, tmax - tmin)) * S
    for t in range(int(tmin), int(tmax) + 1):
        if t % 2 == 0:
            d.line([(x0 * S, Y(t)), (x1 * S, Y(t))], fill=GRID, width=S)
            d.text((2 * S, Y(t) - 6 * S), f"{t}°", font=_font(font, 10), fill=INK)
    bw = (x1 - x0) / n * 0.55
    for i, p in enumerate(pioggia):                       # barre della pioggia
        if p and p > 5:
            h = (y1 - y0) * p / 100 * 0.6
            d.rounded_rectangle([X(i) - bw * S / 2, (y1 - h) * S, X(i) + bw * S / 2, y1 * S],
                                radius=2 * S, fill=(170, 205, 245))
    pts = [(X(i), Y(t)) for i, t in enumerate(temp)]
    d.line(pts, fill=RED, width=3 * S, joint="curve")
    for i, (x, y) in enumerate(pts):
        if i in (0, n - 1) or temp[i] in (max(temp), min(temp)):
            d.ellipse([x - 3 * S, y - 3 * S, x + 3 * S, y + 3 * S], fill=WHITE, outline=RED, width=S)
            d.text((x, y - 6 * S), f"{temp[i]:.0f}°", font=_font(font, 11), fill=INK, anchor="mb")
    step = max(1, n // 6)
    for i in range(0, n, step):
        d.text((X(i), (y1 + 4) * S), ore[i], font=_font(font, 10), fill=INK, anchor="mt")
    return _done(img)


def claude(sessione, settimana, font):
    img, d = _canvas()
    rows = [("5 ore", sessione), ("7 giorni", settimana)]
    for k, (lab, v) in enumerate(rows):
        if v is None:
            continue
        y = 22 + k * 52
        d.text((10 * S, y * S), lab, font=_font(font, 13), fill=INK)
        d.text(((CARD_W - 10) * S, y * S), f"{v:.0f}%", font=_font(font, 13), fill=INK, anchor="ra")
        bx0, bx1, by = 10, CARD_W - 10, y + 20
        d.rounded_rectangle([bx0 * S, by * S, bx1 * S, (by + 16) * S], radius=8 * S, fill=GRID,
                            outline=INK, width=2 * S)
        col = GREEN if v < 60 else YELLOW if v < 80 else RED
        w = (bx1 - bx0 - 4) * min(100, v) / 100
        if w > 6:
            d.rounded_rectangle([(bx0 + 2) * S, (by + 2) * S, (bx0 + 2 + w) * S, (by + 14) * S],
                                radius=6 * S, fill=col)
    return _done(img)


def dollari(x):
    """0.0123 -> '0,01 $', 2 -> '2 $', 2.5 -> '2,50 $' (all'italiana)."""
    x = float(x or 0)
    if 0 < x < 0.01:
        return "meno di 0,01 $"
    t = f"{x:.0f}" if x == int(x) else f"{x:.2f}".replace(".", ",")
    return t + " $"


def budget(speso, tetto, font):
    """La spesa delle API: quanto si e' speso questo mese (e su quanto, se c'e' un budget)."""
    img, d = _canvas()
    d.text((10 * S, 16 * S), "API questo mese", font=_font(font, 13), fill=INK)
    d.text(((CARD_W - 10) * S, 46 * S), dollari(speso), font=_font(font, 22), fill=INK, anchor="ra")
    if tetto:
        v = 100 * speso / tetto
        bx0, bx1, by = 10, CARD_W - 10, 82
        d.rounded_rectangle([bx0 * S, by * S, bx1 * S, (by + 16) * S], radius=8 * S, fill=GRID,
                            outline=INK, width=2 * S)
        col = GREEN if v < 60 else YELLOW if v < 80 else RED
        w = (bx1 - bx0 - 4) * min(100, v) / 100
        if w > 6:
            d.rounded_rectangle([(bx0 + 2) * S, (by + 2) * S, (bx0 + 2 + w) * S, (by + 14) * S],
                                radius=6 * S, fill=col)
        d.text((10 * S, 104 * S), "su " + dollari(tetto), font=_font(font, 11), fill=INK)
    return _done(img)


def radar(aerei, font, raggio_km=25):
    """aerei: lista di dict con km, lat, lon (rispetto a casa: dlat/dlon gia' calcolati come dx,dy in km)."""
    img, d = _canvas()
    cx, cy, r = CARD_W / 2, CARD_H / 2 + 2, CARD_H / 2 - 8
    for k in (1, 2, 3):
        rr = r * k / 3
        d.ellipse([(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S], outline=GRID, width=2 * S)
    d.line([((cx - r) * S, cy * S), ((cx + r) * S, cy * S)], fill=GRID, width=S)
    d.line([(cx * S, (cy - r) * S), (cx * S, (cy + r) * S)], fill=GRID, width=S)
    # casa
    d.polygon([((cx - 5) * S, (cy + 1) * S), ((cx + 5) * S, (cy + 1) * S), (cx * S, (cy - 5) * S)], fill=INK)
    d.rectangle([(cx - 3.5) * S, (cy + 1) * S, (cx + 3.5) * S, (cy + 6) * S], fill=INK)
    d.text(((cx - r) * S, 2 * S), f"{raggio_km} km", font=_font(font, 9), fill=INK)
    d.text(((cx + r) * S, 2 * S), "N", font=_font(font, 10), fill=INK, anchor="ra")
    for i, a in enumerate(aerei[:12]):
        px = cx + a["dx"] / raggio_km * r
        py = cy - a["dy"] / raggio_km * r
        big = i == 0
        rad = 5 if big else 3
        d.ellipse([(px - rad) * S, (py - rad) * S, (px + rad) * S, (py + rad) * S],
                  fill=RED if big else BLUE, outline=INK, width=S)
    return _done(img)


DEFAULT_PALETTE = {
    ".": None, "K": INK, "W": WHITE, "R": RED, "B": BLUE, "Y": YELLOW, "G": GREEN,
    "O": (245, 140, 40), "P": (240, 130, 180), "N": (130, 85, 50), "A": (150, 150, 160),
    "C": (120, 200, 240), "V": (150, 90, 200), "S": (252, 229, 203),
}


def pixel_art(righe, palette=None):
    """righe: lista di stringhe della stessa lunghezza (max 24x24), un carattere per pixel."""
    pal = dict(DEFAULT_PALETTE)
    pal.update(palette or {})
    righe = [r[:24] for r in righe[:24] if r]
    h, w = len(righe), max((len(r) for r in righe), default=0)
    img = Image.new("RGB", (CARD_W, CARD_H), PAPER)
    if not h or not w:
        return img
    cell = max(1, min((CARD_W - 12) // w, (CARD_H - 12) // h))
    ox, oy = (CARD_W - cell * w) // 2, (CARD_H - cell * h) // 2
    d = ImageDraw.Draw(img)
    for y, row in enumerate(righe):
        for x, ch in enumerate(row):
            c = pal.get(ch)
            if c:
                d.rectangle([ox + x * cell, oy + y * cell, ox + (x + 1) * cell - 1, oy + (y + 1) * cell - 1], fill=c)
    return img


# ------------------------------------------------------------------ meteo dei giorni (2.0)
CLOUD = (200, 208, 222)
DROP = (70, 140, 230)


def icona(d, cielo, cx, cy, r):
    """Icona del cielo centrata in (cx, cy), raggio r, in coordinate 1x (si disegna a 4x)."""
    def E(x0, y0, x1, y1, c):
        d.ellipse([x0 * S, y0 * S, x1 * S, y1 * S], fill=c, outline=INK, width=max(1, int(S * .8)))

    def nuvola(c=CLOUD, dy=0):
        E(cx - r, cy - r * .2 + dy, cx + r * .1, cy + r * .6 + dy, c)
        E(cx - r * .55, cy - r * .7 + dy, cx + r * .45, cy + r * .4 + dy, c)
        E(cx - r * .1, cy - r * .35 + dy, cx + r, cy + r * .6 + dy, c)
        d.rectangle([(cx - r * .7) * S, (cy + r * .05 + dy) * S, (cx + r * .75) * S, (cy + r * .55 + dy) * S], fill=c)

    if cielo == "sole":
        for k in range(8):
            a = math.radians(k * 45)
            d.line([((cx + math.cos(a) * r * .7) * S, (cy + math.sin(a) * r * .7) * S),
                    ((cx + math.cos(a) * r) * S, (cy + math.sin(a) * r) * S)], fill=YELLOW, width=int(S * 1.4))
        E(cx - r * .5, cy - r * .5, cx + r * .5, cy + r * .5, YELLOW)
    elif cielo == "nebbia":
        for k in range(3):
            y = cy - r * .5 + k * r * .5
            d.line([((cx - r) * S, y * S), ((cx + r) * S, y * S)], fill=(150, 160, 175), width=int(S * 1.6))
    else:
        nuvola(dy=-r * .25)
        if cielo == "pioggia":
            for k in (-1, 0, 1):
                x = cx + k * r * .5
                d.line([(x * S, (cy + r * .55) * S), ((x - r * .15) * S, (cy + r * .95) * S)], fill=DROP,
                       width=int(S * 1.5))
        elif cielo == "neve":
            for k in (-1, 0, 1):
                x, y = cx + k * r * .5, cy + r * .8
                d.ellipse([(x - r * .12) * S, (y - r * .12) * S, (x + r * .12) * S, (y + r * .12) * S],
                          fill=WHITE, outline=DROP, width=S)
        elif cielo == "temporale":
            d.polygon([((cx + r * .1) * S, (cy + r * .3) * S), ((cx - r * .25) * S, (cy + r * .75) * S),
                       ((cx + r * .02) * S, (cy + r * .72) * S), ((cx - r * .15) * S, (cy + r * 1.1) * S),
                       ((cx + r * .35) * S, (cy + r * .55) * S), ((cx + r * .08) * S, (cy + r * .58) * S)],
                      fill=YELLOW)


def settimana(giorni, oggi, font, prima=3, dopo=3, w=CARD_W, h=CARD_H, titolo=None):
    """giorni: lista di meteo.giorni(); oggi: il suo indice. Una colonna per giorno (da oggi-prima
    a oggi+dopo): nome, cielo, barretta dalla minima alla massima. Oggi su fondo evidenziato."""
    import meteo
    img, d = _canvas(w, h)
    a, b = max(0, oggi - prima), min(len(giorni), oggi + dopo + 1)
    gg = [g for g in giorni[a:b] if g["tmax"] is not None and g["tmin"] is not None]
    if not gg:
        return _done(img)
    n = len(gg)
    top = 0
    if titolo:
        d.text((w / 2 * S, 4 * S), titolo, font=_font(font, 13), fill=INK, anchor="mt")
        top = 20
    cw = (w - 4) / n
    k = max(9, min(13, int(cw / 2.3)))                       # misura del testo
    y_nome, y_ico = top + 3, top + 3 + k + cw * .32 + 2
    y0, y1 = y_ico + cw * .36 + k + 4, h - k - 6               # spazio della barretta
    lo = min(g["tmin"] for g in gg) - 1
    hi = max(g["tmax"] for g in gg) + 1

    def Y(t):
        return y1 - (y1 - y0) * (t - lo) / max(1, hi - lo)
    for j, g in enumerate(gg):
        cx = 2 + cw * (j + .5)
        idx = a + giorni[a:b].index(g)
        if idx == oggi:
            d.rounded_rectangle([(cx - cw / 2 + 1) * S, (top + 1) * S, (cx + cw / 2 - 1) * S, (h - 2) * S],
                                radius=5 * S, fill=(255, 236, 190))
        nome = "oggi" if idx == oggi else (meteo.BREVI[g["data"].weekday()] if g["data"] else f"{idx - oggi:+d}")
        passato = idx < oggi
        col = (120, 140, 165) if passato else INK
        d.text((cx * S, y_nome * S), nome, font=_font(font, k), fill=col, anchor="mt")
        icona(d, meteo.cielo(g), cx, y_ico, cw * .32)
        bx = max(3, cw * .16)
        d.rounded_rectangle([(cx - bx) * S, Y(g["tmax"]) * S, (cx + bx) * S, max(Y(g["tmin"]), Y(g["tmax"]) + 2) * S],
                            radius=bx * S, fill=(150, 175, 205) if passato else RED, outline=INK, width=S)
        d.text((cx * S, (Y(g["tmax"]) - 2) * S), f"{g['tmax']:.0f}", font=_font(font, k), fill=col, anchor="mb")
        d.text((cx * S, (Y(g["tmin"]) + 2) * S), f"{g['tmin']:.0f}", font=_font(font, k), fill=col, anchor="mt")
    return _done(img)


# ------------------------------------------------------------------ schermate a tutto cubo (2.0)
FULL_W, FULL_H = 240, 200


def _titolo(d, testo, font, w=FULL_W):
    d.text((w / 2 * S, 6 * S), testo, font=_font(font, 15), fill=INK, anchor="mt")


def schermata_casa(persone, stanze, luci, font):
    """persone: [(nome, in_casa)]; stanze: [(nome, gradi, variazione_in_un'ora o None)];
    luci: quante luci accese."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, "In casa", font)
    y = 30
    for k, (nome, dentro) in enumerate(persone[:6]):
        x = 14 + (k % 3) * 74
        yy = y + (k // 3) * 22
        d.ellipse([x * S, (yy + 3) * S, (x + 10) * S, (yy + 13) * S], fill=GREEN if dentro else GRID,
                  outline=INK, width=S)
        d.text(((x + 15) * S, (yy + 8) * S), nome[:8], font=_font(font, 12),
               fill=INK if dentro else (130, 145, 165), anchor="lm")
    y = 30 + 22 * ((min(len(persone), 6) + 2) // 3) + 8
    d.line([(10 * S, y * S), ((FULL_W - 10) * S, y * S)], fill=GRID, width=S)
    y += 8
    for nome, t, dv in stanze[:5]:
        d.text((14 * S, y * S), nome[:16], font=_font(font, 13), fill=INK)
        d.text((178 * S, y * S), f"{t:.1f}°".replace(".", ","), font=_font(font, 13), fill=INK, anchor="ra")
        if dv is not None and abs(dv) >= .3:
            up = dv > 0
            col = RED if up else BLUE
            cx, cy = 194, y + 8
            k = 1 if up else -1                               # triangolo in su o in giu'
            pts = [(cx - 5, cy + 3 * k), (cx + 5, cy + 3 * k), (cx, cy - 4 * k)]
            d.polygon([(px * S, py * S) for px, py in pts], fill=col)
            d.text((204 * S, y * S), f"{abs(dv):.1f}".replace(".", ","), font=_font(font, 11), fill=col)
        y += 20
    d.text((FULL_W / 2 * S, (FULL_H - 6) * S),
           "nessuna luce accesa" if not luci else f"{luci} luc{'e accesa' if luci == 1 else 'i accese'}",
           font=_font(font, 12), fill=INK, anchor="mb")
    return _done(img)


def schermata_consumi(watt, kwh_oggi, kwh_ieri, font):
    """La casa adesso (watt) e l'energia di oggi, con quella di ieri per confronto."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, "Corrente", font)
    if watt is not None:
        d.text((FULL_W / 2 * S, 62 * S), f"{watt:.0f} W", font=_font(font, 34), fill=INK, anchor="mm")
        d.text((FULL_W / 2 * S, 88 * S), "adesso", font=_font(font, 11), fill=(130, 145, 165), anchor="mm")
    if kwh_oggi is not None:
        top = max(kwh_oggi, kwh_ieri or 0, 0.1)
        for k, (lab, v) in enumerate((("oggi", kwh_oggi), ("ieri", kwh_ieri))):
            if v is None:
                continue
            y = 112 + k * 38
            d.text((14 * S, y * S), lab, font=_font(font, 12), fill=INK)
            d.text(((FULL_W - 14) * S, y * S), f"{v:.1f} kWh".replace(".", ","), font=_font(font, 12),
                   fill=INK, anchor="ra")
            d.rounded_rectangle([14 * S, (y + 17) * S, (FULL_W - 14) * S, (y + 29) * S], radius=6 * S,
                                fill=GRID, outline=INK, width=S)
            wv = (FULL_W - 32) * min(1, v / top)
            if wv > 5:
                d.rounded_rectangle([16 * S, (y + 19) * S, (16 + wv) * S, (y + 27) * S], radius=4 * S,
                                    fill=YELLOW if k == 0 else (170, 185, 205))
    return _done(img)
