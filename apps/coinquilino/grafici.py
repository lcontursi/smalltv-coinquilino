"""
Grafici e disegni che Alessio mostra sulla sua lavagnetta.

Tutte le funzioni restituiscono un'immagine RGB di CARD_W x CARD_H, disegnata a 4x
e ridotta con antialias, nello stesso stile dello sticker (contorni blu, colori pieni).

  temperature(ore, temp, pioggia, font)   prossime ore: linea delle temperature + barre pioggia
  claude(sessione, settimana, font)       due barre dei consumi
  radar(aerei, font)                      aerei intorno a casa (puntini, il piu' vicino evidenziato)
  pixel_art(righe, palette)               disegno di Claude: griglia di caratteri -> colori
  disegno(righe)                          (3.1.1) disegno di Claude a forme (o pixel art se vecchio)
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
GRIGIO = (130, 145, 165)
ORANGE = (240, 140, 50)

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


TITOLO_CARD = 20        # 3.5: spazio del titolo sulle lavagnette


def _titolo(d, testo, font, w=None):
    """Il titolo, centrato in alto: 15 px sulle schermate a tutto cubo, 11 sulle lavagnette."""
    w = w or FULL_W
    card = w < FULL_W
    d.text((w / 2 * S, (3 if card else 6) * S), testo, font=_font(font, 13 if card else 16), fill=INK, anchor="mt")


def _barra(d, x0, y, x1, h, frazione, colore):
    """Una barra di livello: fondo grigio con bordo, dentro il colore (stessa per tutte)."""
    d.rounded_rectangle([x0 * S, y * S, x1 * S, (y + h) * S], radius=h / 2 * S, fill=GRID, outline=INK, width=S)
    w = (x1 - x0 - 4) * max(0.0, min(1.0, frazione))
    if w > h - 4:
        d.rounded_rectangle([(x0 + 2) * S, (y + 2) * S, (x0 + 2 + w) * S, (y + h - 2) * S], radius=(h - 4) / 2 * S,
                            fill=colore)


def temperature(ore, temp, pioggia, font):
    """ore: ['14', '15', ...]; temp: gradi; pioggia: probabilita' % (stessa lunghezza)."""
    img, d = _canvas()
    _titolo(d, "Prossime ore", font, CARD_W)
    n = len(temp)
    if n < 2:
        return _done(img)
    x0, x1, y0, y1 = 22, CARD_W - 8, TITOLO_CARD + 8, CARD_H - 18
    tmin, tmax = math.floor(min(temp)) - 1, math.ceil(max(temp)) + 1
    def X(i): return (x0 + (x1 - x0) * i / (n - 1)) * S
    def Y(t): return (y1 - (y1 - y0) * (t - tmin) / max(1, tmax - tmin)) * S
    for t in range(int(tmin), int(tmax) + 1):
        if t % 2 == 0:
            d.line([(x0 * S, Y(t)), (x1 * S, Y(t))], fill=GRID, width=S)
            d.text((2 * S, Y(t) - 6 * S), f"{t}°", font=_font(font, 11), fill=INK)
    bw = (x1 - x0) / n * 0.55
    for i, p in enumerate(pioggia):                       # barre della pioggia
        if p and p > 5:
            h = (y1 - y0) * p / 100 * 0.6
            d.rounded_rectangle([X(i) - bw * S / 2, (y1 - h) * S, X(i) + bw * S / 2, y1 * S],
                                radius=2 * S, fill=(170, 205, 245))
    pts = [(X(i), Y(t)) for i, t in enumerate(temp)]
    d.line(pts, fill=RED, width=3 * S, joint="curve")
    segnati = {0, n - 1, temp.index(max(temp)), temp.index(min(temp))}   # 3.5: il massimo una volta sola
    for i, (x, y) in enumerate(pts):
        if i in segnati:
            d.ellipse([x - 3 * S, y - 3 * S, x + 3 * S, y + 3 * S], fill=WHITE, outline=RED, width=S)
            # agli estremi l'etichetta va verso l'interno, per non coprire i gradi dell'asse
            anchor = "lb" if i == 0 else "rb" if i == n - 1 else "mb"
            d.text((x + (2 * S if i == 0 else 0), y - 6 * S), f"{temp[i]:.0f}°", font=_font(font, 12), fill=INK,
                   anchor=anchor)
    step = max(1, n // 6)
    for i in range(0, n, step):
        d.text((X(i), (y1 + 4) * S), ore[i], font=_font(font, 11), fill=INK, anchor="mt")
    return _done(img)


def claude(sessione, settimana, font):
    img, d = _canvas()
    _titolo(d, "Claude", font, CARD_W)
    rows = [("5 ore", sessione), ("7 giorni", settimana)]
    for k, (lab, v) in enumerate(rows):
        if v is None:
            continue
        y = TITOLO_CARD + 12 + k * 46
        d.text((10 * S, y * S), lab, font=_font(font, 13), fill=INK)
        d.text(((CARD_W - 10) * S, y * S), f"{v:.0f}%", font=_font(font, 13), fill=INK, anchor="ra")
        _barra(d, 10, y + 20, CARD_W - 10, 14, v / 100, GREEN if v < 60 else YELLOW if v < 80 else RED)
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
    _titolo(d, "API questo mese", font, CARD_W)
    d.text((CARD_W / 2 * S, (56 if tetto else CARD_H / 2 + 8) * S), dollari(speso), font=_font(font, 26), fill=INK,
           anchor="mm")
    if tetto:
        v = 100 * speso / tetto
        _barra(d, 10, 80, CARD_W - 10, 14, v / 100, GREEN if v < 60 else YELLOW if v < 80 else RED)
        d.text((CARD_W / 2 * S, 100 * S), "su " + dollari(tetto), font=_font(font, 13), fill=GRIGIO, anchor="mt")
    return _done(img)


def radar(aerei, font, raggio_km=25):
    """aerei: lista di dict con km, lat, lon (rispetto a casa: dlat/dlon gia' calcolati come dx,dy in km)."""
    img, d = _canvas()
    _titolo(d, "Aerei qui intorno", font, CARD_W)
    cx, cy, r = CARD_W / 2, (CARD_H + TITOLO_CARD) / 2, (CARD_H - TITOLO_CARD) / 2 - 4
    for k in (1, 2, 3):
        rr = r * k / 3
        d.ellipse([(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S], outline=GRID, width=2 * S)
    d.line([((cx - r) * S, cy * S), ((cx + r) * S, cy * S)], fill=GRID, width=S)
    d.line([(cx * S, (cy - r) * S), (cx * S, (cy + r) * S)], fill=GRID, width=S)
    # casa
    d.polygon([((cx - 5) * S, (cy + 1) * S), ((cx + 5) * S, (cy + 1) * S), (cx * S, (cy - 5) * S)], fill=INK)
    d.rectangle([(cx - 3.5) * S, (cy + 1) * S, (cx + 3.5) * S, (cy + 6) * S], fill=INK)
    d.text((8 * S, (CARD_H - 4) * S), f"{raggio_km} km", font=_font(font, 12), fill=GRIGIO, anchor="lb")
    d.text((cx * S, (cy - r - 1) * S), "N", font=_font(font, 11), fill=GRIGIO, anchor="mb")
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


# ------------------------------------------------------------------ disegni a forme (3.1.1, CM)
# Un ragazzino di 10 anni non disegna a quadretti: disegna con i pennarelli. Claude scrive forme
# semplici su un foglio da 160 x 120 e qui diventano un disegno con il contorno, come i grafici.
COLORI = {"nero": (35, 35, 45), "scuro": INK, "bianco": WHITE, "rosso": RED, "blu": BLUE,
          "giallo": YELLOW, "verde": GREEN, "verdescuro": (40, 110, 60), "arancione": (245, 140, 40),
          "rosa": (240, 130, 180), "marrone": (130, 85, 50), "grigio": (150, 150, 160),
          "azzurro": (120, 200, 240), "viola": (150, 90, 200), "pelle": (252, 229, 203),
          "beige": (235, 215, 170), "oro": (230, 180, 50), "celeste": (200, 230, 250)}
FOGLIO_W, FOGLIO_H = 160, 120
MAX_FORME = 80


def forme(righe):
    """Le righe del disegno -> lista di forme valide (comando, colore, numeri). Le righe che non
    si capiscono si saltano: la chiamata e' gia' pagata."""
    out = []
    for r in righe:
        p = str(r).lower().replace(",", " ").split()
        if not p:
            continue
        cmd, rest = p[0], p[1:]
        col = next((COLORI[x] for x in rest if x in COLORI), None)
        nums = []
        for x in rest:
            try:
                nums.append(float(x))
            except ValueError:
                pass
        need = {"sfondo": 0, "rett": 4, "cerchio": 3, "ellisse": 4, "linea": 4, "poli": 6}.get(cmd)
        if need is None or col is None or len(nums) < need:
            continue
        if cmd == "poli" and len(nums) % 2:
            nums = nums[:-1]
        out.append((cmd, col, nums))
    return out[:MAX_FORME]


def disegno(righe):
    """Il disegno di Claude -> lavagnetta. Forme (3.1.1) se ce ne sono almeno 3, altrimenti la
    vecchia griglia in pixel art (i disegni salvati in galleria prima della 3.1.1)."""
    fs = forme(righe)
    if len(fs) < 3:
        return pixel_art(righe)
    img, d = _canvas()
    k = min(CARD_W / FOGLIO_W, CARD_H / FOGLIO_H) * S
    ox, oy = (CARD_W * S - FOGLIO_W * k) / 2, (CARD_H * S - FOGLIO_H * k) / 2

    def P(x, y):
        return (ox + max(0.0, min(FOGLIO_W, x)) * k, oy + max(0.0, min(FOGLIO_H, y)) * k)
    bordo = max(1, int(S * 0.9))
    for cmd, col, n in fs:
        if cmd == "sfondo":
            d.rectangle([P(0, 0), P(FOGLIO_W, FOGLIO_H)], fill=col)
        elif cmd == "rett":
            (x0, y0), (x1, y1) = P(min(n[0], n[2]), min(n[1], n[3])), P(max(n[0], n[2]), max(n[1], n[3]))
            d.rectangle([x0, y0, x1, y1], fill=col, outline=INK, width=bordo)
        elif cmd == "ellisse":
            (x0, y0), (x1, y1) = P(min(n[0], n[2]), min(n[1], n[3])), P(max(n[0], n[2]), max(n[1], n[3]))
            d.ellipse([x0, y0, x1, y1], fill=col, outline=INK, width=bordo)
        elif cmd == "cerchio":
            (x0, y0), (x1, y1) = P(n[0] - n[2], n[1] - n[2]), P(n[0] + n[2], n[1] + n[2])
            d.ellipse([x0, y0, x1, y1], fill=col, outline=INK, width=bordo)
        elif cmd == "linea":
            w = int(max(1.0, min(8.0, n[4] if len(n) > 4 else 2.0)) * k)
            d.line([P(n[0], n[1]), P(n[2], n[3])], fill=col, width=w, joint="curve")
        elif cmd == "poli":
            d.polygon([P(n[i], n[i + 1]) for i in range(0, len(n), 2)], fill=col, outline=INK, width=bordo)
    return _done(img)


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
    titolo = titolo or "La settimana"
    _titolo(d, titolo, font, w)
    top = TITOLO_CARD if w < FULL_W else 24
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
# 3.4 (DC): 220x180, come le foto: il personaggio le mette nella stessa cornice bianca sulla cameretta
FULL_W, FULL_H = 220, 180


def schermata_casa(persone, stanze, luci, font):
    """persone: [(nome, in_casa)]; stanze: [(nome, gradi, variazione_in_un'ora o None)];
    luci: quante luci accese."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, "In casa", font)
    y = 30
    for k, (nome, dentro) in enumerate(persone[:6]):
        x = 10 + (k % 3) * (FULL_W - 20) / 3
        yy = y + (k // 3) * 22
        d.ellipse([x * S, (yy + 3) * S, (x + 10) * S, (yy + 13) * S], fill=GREEN if dentro else GRID,
                  outline=INK, width=S)
        px, larg = 14, (FULL_W - 20) / 3 - 18
        while px > 8 and d.textlength(nome[:12], font=_font(font, px)) / S > larg:
            px -= 1                                          # il nome lungo si rimpicciolisce
        d.text(((x + 15) * S, (yy + 8) * S), nome[:12], font=_font(font, px),
               fill=INK if dentro else (130, 145, 165), anchor="lm")
    y = 30 + 22 * ((min(len(persone), 6) + 2) // 3) + 8
    d.line([(10 * S, y * S), ((FULL_W - 10) * S, y * S)], fill=GRID, width=S)
    y += 8
    for nome, t, dv in stanze[:max(0, int((FULL_H - 22 - y) / 20))]:   # quante ne stanno sopra le luci
        d.text((14 * S, y * S), nome[:16], font=_font(font, 15), fill=INK)
        d.text(((FULL_W - 50) * S, y * S), f"{t:.1f}°".replace(".", ","), font=_font(font, 15), fill=INK, anchor="ra")
        if dv is not None and abs(dv) >= .3:
            up = dv > 0
            col = RED if up else BLUE
            cx, cy = FULL_W - 36, y + 8
            k = 1 if up else -1                               # triangolo in su o in giu'
            pts = [(cx - 5, cy + 3 * k), (cx + 5, cy + 3 * k), (cx, cy - 4 * k)]
            d.polygon([(px * S, py * S) for px, py in pts], fill=col)
            d.text(((FULL_W - 27) * S, y * S), f"{abs(dv):.1f}".replace(".", ","), font=_font(font, 13), fill=col)
        y += 20
    d.text((FULL_W / 2 * S, (FULL_H - 6) * S),
           "nessuna luce accesa" if not luci else f"{luci} luc{'e accesa' if luci == 1 else 'i accese'}",
           font=_font(font, 14), fill=INK, anchor="mb")
    return _done(img)


def schermata_consumi(watt, kwh_oggi, kwh_ieri, font):
    """La casa adesso (watt) e l'energia di oggi, con quella di ieri per confronto."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, "Corrente", font)
    if watt is not None:
        d.text((FULL_W / 2 * S, 62 * S), f"{watt:.0f} W", font=_font(font, 34), fill=INK, anchor="mm")
        d.text((FULL_W / 2 * S, 88 * S), "adesso", font=_font(font, 13), fill=(130, 145, 165), anchor="mm")
    if kwh_oggi is not None:
        top = max(kwh_oggi, kwh_ieri or 0, 0.1)
        for k, (lab, v) in enumerate((("oggi", kwh_oggi), ("ieri", kwh_ieri))):
            if v is None:
                continue
            y = 104 + k * 36
            d.text((14 * S, y * S), lab, font=_font(font, 14), fill=INK)
            d.text(((FULL_W - 14) * S, y * S), f"{v:.1f} kWh".replace(".", ","), font=_font(font, 14),
                   fill=INK, anchor="ra")
            _barra(d, 14, y + 17, FULL_W - 14, 14, v / top, YELLOW if k == 0 else (170, 185, 205))
    return _done(img)


# ------------------------------------------------------------------ widget e griglia (3.4)
# Una schermata e' fatta di celle (rettangoli) e di widget che si disegnano dentro una cella:
# `griglia` dice dove stanno le celle, `w_anello` e `w_valore` cosa c'e' dentro. Cosi' una schermata
# nuova e' poche righe e il bordo (DC) potra' stare in un punto solo.
class Cella:
    """Un rettangolo dello schermo, in pixel veri (non ingranditi)."""
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2


def griglia(n, w=FULL_W, h=FULL_H, alto=28, basso=6, margine=8, spazio=6, colonne=None):
    """Le celle di n elementi uguali sotto il titolo: 1, 2, 3 in fila; 4 in 2x2; 5-6 in 3 colonne;
    poi 4 colonne. L'ultima riga, se e' incompleta, sta al centro."""
    if n <= 0:
        return []
    cols = colonne or {1: 1, 2: 2, 3: 3, 4: 2, 5: 3, 6: 3}.get(n, 4)
    righe = -(-n // cols)
    cw = (w - 2 * margine - (cols - 1) * spazio) / cols
    ch = (h - alto - basso - (righe - 1) * spazio) / righe
    celle = []
    for r in range(righe):
        in_riga = min(cols, n - r * cols)
        x0 = margine + (cols - in_riga) * (cw + spazio) / 2
        for k in range(in_riga):
            celle.append(Cella(x0 + k * (cw + spazio), alto + r * (ch + spazio), cw, ch))
    return celle


def colore_livello(p):
    """Rosso sotto il 20%, giallo sotto il 40%, verde sopra."""
    return RED if p < 20 else YELLOW if p < 40 else GREEN


def w_anello(d, c, valore, nome, font, colore=None):
    """Un anello che si riempie fino a `valore` (0-100), la percentuale al centro, il nome sotto."""
    px_nome = 13 if c.w < 90 else 14
    r = max(10, min(c.w / 2 - 3, (c.h - px_nome - 8) / 2, 52))
    cx, cy = c.cx, c.cy - (px_nome + 4) / 2                 # anello + nome, al centro della cella
    larg = max(4, r * .3)
    box = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]
    d.ellipse(box, outline=GRID, width=int(larg * S))
    v = max(0, min(100, valore))
    if v > 0:
        d.arc(box, -90, -90 + 360 * v / 100, fill=colore or colore_livello(v), width=int(larg * S))
    d.text((cx * S, cy * S), f"{v:.0f}%", font=_font(font, max(9, int(r * .56))), fill=INK, anchor="mm")
    while px_nome > 9 and d.textlength(nome, font=_font(font, px_nome)) / S > c.w:
        px_nome -= 1                                          # il nome lungo si rimpicciolisce
    d.text((cx * S, (cy + r + 4) * S), nome, font=_font(font, px_nome), fill=INK, anchor="mt")


def w_valore(d, c, testo, etichetta, font, px=22, colore=INK):
    """Un numero grande con la sua etichetta sotto, al centro della cella."""
    d.text((c.cx * S, (c.cy - 6) * S), testo, font=_font(font, px), fill=colore, anchor="mm")
    d.text((c.cx * S, (c.cy + px / 2 + 2) * S), etichetta, font=_font(font, 13), fill=GRIGIO, anchor="mt")


def _etichetta(d, x, y, testo, font, colore, px=12):
    """Una pastiglia colorata col testo; restituisce dove finisce (x del bordo destro)."""
    f = _font(font, px)
    larg = d.textlength(testo, font=f) / S + 14
    d.rounded_rectangle([x * S, y * S, (x + larg) * S, (y + px + 8) * S], radius=(px + 8) / 2 * S,
                        fill=colore)
    d.text(((x + larg / 2) * S, (y + (px + 8) / 2) * S), testo, font=f, fill=WHITE, anchor="mm")
    return x + larg


def schermata_batterie(voci, font):
    """voci: [(nome, percento)], dalla piu' scarica. Un anello per dispositivo, al massimo 8."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, "Batterie", font)
    voci = sorted(voci, key=lambda v: v[1])[:8]
    for c, (nome, p) in zip(griglia(len(voci)), voci, strict=True):
        w_anello(d, c, p, nome[:14], font)
    return _done(img)


def schermata_termostato(attuale, obiettivo, azione, umidita, stanze, font):
    """attuale/obiettivo: gradi; azione: 'heating' | 'cooling' | 'idle' | None; umidita: % o None;
    stanze: [(nome, gradi)], le altre stanze (al massimo 3)."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, "Termostato", font)
    d.text((FULL_W / 2 * S, 62 * S), f"{attuale:.1f}°".replace(".", ","), font=_font(font, 46), fill=INK,
           anchor="mm")
    voci = []
    if azione == "heating":
        voci.append(("riscalda", ORANGE))
    elif azione == "cooling":
        voci.append(("raffredda", BLUE))
    elif azione is not None:
        voci.append(("fermo", (150, 165, 185)))
    if obiettivo is not None:
        voci.append((f"a {obiettivo:.1f}°".replace(".", ",").replace(",0°", "°"), INK))
    if umidita is not None:
        voci.append((f"umidità {umidita:.0f}%", (110, 160, 210)))
    f = _font(font, 13)
    def largo(vv):
        return sum(d.textlength(t, font=f) / S + 14 for t, _ in vv) + 6 * (len(vv) - 1)
    while len(voci) > 1 and largo(voci) > FULL_W - 12:
        voci.pop()                                          # non ci sta: via l'ultima (l'umidita')
    totale = largo(voci)
    x = (FULL_W - totale) / 2
    for t, col in voci:
        x = _etichetta(d, x, 94, t, font, col, px=13) + 6
    if stanze:
        d.line([(10 * S, 124 * S), ((FULL_W - 10) * S, 124 * S)], fill=GRID, width=S)
        for c, (nome, t) in zip(griglia(len(stanze[:3]), alto=128, basso=2), stanze[:3], strict=True):
            w_valore(d, c, f"{t:.1f}°".replace(".", ","), nome[:12], font, px=20)
    return _done(img)


# ------------------------------------------------------------------ altre schermate (3.5, DA, CV, CX)
def _testo_largo(d, testo, font, px, larg, minimo=9):
    """La misura piu' grande (fino a `minimo`) con cui `testo` sta in `larg` pixel."""
    while px > minimo and d.textlength(testo, font=_font(font, px)) / S > larg:
        px -= 1
    return px


def _righe(d, testo, font, px, larg, massimo=4):
    """Il testo diviso in righe che stanno in `larg` pixel (al massimo `massimo`, l'ultima con …)."""
    f = _font(font, px)
    righe, riga = [], ""
    for p in testo.split():
        prova = (riga + " " + p).strip()
        if riga and d.textlength(prova, font=f) / S > larg:
            righe.append(riga)
            riga = p
        else:
            riga = prova
    if riga:
        righe.append(riga)
    if len(righe) > massimo:
        righe = righe[:massimo]
        righe[-1] = righe[-1].rstrip(".,;:") + "…"
    return righe


def schermata_orologio(ora, data, esterno, appuntamento, font):
    """ora: "14:05"; data: "sabato 15 novembre"; esterno: (cielo, gradi) o None;
    appuntamento: (quando, cosa) o None, il prossimo dei calendari."""
    img, d = _canvas(FULL_W, FULL_H)
    d.text((FULL_W / 2 * S, 46 * S), ora, font=_font(font, 54), fill=INK, anchor="mm")
    d.text((FULL_W / 2 * S, 84 * S), data, font=_font(font, _testo_largo(d, data, font, 16, FULL_W - 20)),
           fill=GRIGIO, anchor="mm")
    y = 100
    if esterno:
        cielo, t = esterno
        testo = "fuori" if t is None else f"fuori {t:.0f}°"
        larg = d.textlength(testo, font=_font(font, 18)) / S
        x0 = (FULL_W - larg - 34) / 2
        icona(d, cielo, x0 + 14, y + 14, 13)
        d.text(((x0 + 34) * S, (y + 14) * S), testo, font=_font(font, 18), fill=INK, anchor="lm")
        y += 34
    if appuntamento:
        quando, cosa = appuntamento
        d.line([(10 * S, y * S), ((FULL_W - 10) * S, y * S)], fill=GRID, width=S)
        d.text((FULL_W / 2 * S, (y + 6) * S), quando, font=_font(font, 14), fill=ORANGE, anchor="mt")
        cosa = cosa[:40]
        d.text((FULL_W / 2 * S, (y + 22) * S), cosa,
               font=_font(font, _testo_largo(d, cosa, font, 17, FULL_W - 16)), fill=INK, anchor="mt")
    return _done(img)


def _w_icona(d, c, tipo, acceso):
    """Le icone della casa: luce, clima, termometro, goccia, porta. Accesa = colorata."""
    r = min(c.w * .24, (c.h - 40) / 2.2)
    cx, cy = c.cx, c.cy - 15                                # icona, valore ed etichetta al centro
    lw = max(1, int(S * 1.2))

    def P(x, y):
        return (x * S, y * S)
    if tipo == "luce":
        d.ellipse([P(cx - r * .7, cy - r), P(cx + r * .7, cy + r * .4)], fill=YELLOW if acceso else GRID,
                  outline=INK, width=lw)
        d.rectangle([P(cx - r * .35, cy + r * .4), P(cx + r * .35, cy + r * .8)], fill=GRIGIO, outline=INK,
                    width=lw)
    elif tipo == "clima":
        col = ORANGE if acceso else GRIGIO
        for k in range(6):
            a = math.radians(k * 60)
            d.line([P(cx, cy), P(cx + math.cos(a) * r, cy + math.sin(a) * r)], fill=col, width=int(S * 2))
        d.ellipse([P(cx - r * .25, cy - r * .25), P(cx + r * .25, cy + r * .25)], fill=WHITE, outline=INK,
                  width=lw)
    elif tipo == "termometro":
        d.rounded_rectangle([P(cx - r * .22, cy - r), P(cx + r * .22, cy + r * .4)], radius=r * .22 * S,
                            fill=WHITE, outline=INK, width=lw)
        d.ellipse([P(cx - r * .42, cy + r * .2), P(cx + r * .42, cy + r * 1.0)], fill=RED, outline=INK, width=lw)
        d.rectangle([P(cx - r * .1, cy - r * .3), P(cx + r * .1, cy + r * .4)], fill=RED)
    elif tipo == "goccia":
        d.polygon([P(cx, cy - r), P(cx - r * .6, cy + r * .1), P(cx + r * .6, cy + r * .1)], fill=BLUE)
        d.ellipse([P(cx - r * .6, cy - r * .3), P(cx + r * .6, cy + r * .9)], fill=BLUE, outline=INK, width=lw)
    else:                                                   # porta (o finestra)
        d.rectangle([P(cx - r * .55, cy - r), P(cx + r * .55, cy + r)], fill=ORANGE if acceso else GRID,
                    outline=INK, width=lw)
        d.ellipse([P(cx + r * .2, cy - r * .08), P(cx + r * .36, cy + r * .08)], fill=INK)


def schermata_icone(voci, font):
    """La casa a icone. voci: [(tipo, valore, etichetta, acceso)], al massimo 6;
    tipo: luce | clima | termometro | goccia | porta."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, "La casa", font)
    voci = voci[:6]
    for c, (tipo, valore, etichetta, acceso) in zip(griglia(len(voci)), voci, strict=True):
        _w_icona(d, c, tipo, acceso)
        y = c.cy - 15 + min(c.w * .24, (c.h - 40) / 2.2) + 4
        v = str(valore)
        d.text((c.cx * S, y * S), v, font=_font(font, _testo_largo(d, v, font, 18, c.w)), fill=INK, anchor="mt")
        d.text((c.cx * S, (y + 20) * S), etichetta,
               font=_font(font, _testo_largo(d, etichetta, font, 13, c.w)), fill=GRIGIO, anchor="mt")
    return _done(img)


def _mmss(s):
    s = max(0, int(s))
    return f"{s // 60}:{s % 60:02d}"


def schermata_musica(copertina, titolo, artista, album, posizione, durata, in_pausa, font):
    """In riproduzione (CV): copertina (immagine o None), titolo, artista, album; posizione e durata in
    secondi (o None); in_pausa."""
    img, d = _canvas(FULL_W, FULL_H)
    lato, x0, y0 = 84, 10, 12
    if copertina is not None:
        cop = copertina.convert("RGB").resize((lato * S, lato * S), Image.LANCZOS)
        img.paste(cop, (x0 * S, y0 * S))
        d.rectangle([x0 * S, y0 * S, (x0 + lato) * S, (y0 + lato) * S], outline=INK, width=S)
    else:
        d.rounded_rectangle([x0 * S, y0 * S, (x0 + lato) * S, (y0 + lato) * S], radius=8 * S, fill=GRID,
                            outline=INK, width=S)
        cx, cy = x0 + lato / 2, y0 + lato / 2                # una nota
        d.ellipse([(cx - 16) * S, (cy + 6) * S, (cx - 2) * S, (cy + 18) * S], fill=INK)
        d.rectangle([(cx - 4) * S, (cy - 22) * S, (cx - 1) * S, (cy + 12) * S], fill=INK)
        d.polygon([((cx - 1) * S, (cy - 22) * S), ((cx + 16) * S, (cy - 12) * S), ((cx - 1) * S, (cy - 10) * S)],
                  fill=INK)
    tx = x0 + lato + 10
    larg = FULL_W - tx - 8
    _etichetta(d, tx, y0 + 2, "in pausa" if in_pausa else "in riproduzione", font,
               GRIGIO if in_pausa else GREEN, px=11)
    y = y0 + 28
    for testo, px, col in ((artista, 15, INK), (album, 13, GRIGIO)):
        for r in _righe(d, testo or "", font, px, larg, massimo=2):
            d.text((tx * S, y * S), r, font=_font(font, px), fill=col)
            y += px + 4
    yt = y0 + lato + 8
    for r in _righe(d, titolo or "?", font, 19, FULL_W - 20, massimo=2):
        d.text((FULL_W / 2 * S, yt * S), r, font=_font(font, _testo_largo(d, r, font, 19, FULL_W - 20)),
               fill=INK, anchor="mt")
        yt += 23
    if durata:
        pos = max(0, min(durata, posizione or 0))
        yb = FULL_H - 24
        _barra(d, 12, yb - 2, FULL_W - 12, 10, pos / durata, ORANGE)
        d.text((12 * S, (yb + 10) * S), _mmss(pos), font=_font(font, 12), fill=GRIGIO)
        d.text(((FULL_W - 12) * S, (yb + 10) * S), "-" + _mmss(durata - pos), font=_font(font, 12), fill=GRIGIO,
               anchor="ra")
    return _done(img)


def schermata_porte(voci, font):
    """Porte, finestre e movimento. voci: [(nome, aperto_o_movimento, tipo)], tipo door|window|motion;
    prima quelle aperte, al massimo 7."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, "Porte e finestre", font)
    voci = sorted(voci, key=lambda v: not v[1])[:7]
    passo = 20 if len(voci) > 5 else 26
    y = 28 + (FULL_H - 28 - 4 - passo * len(voci)) / 2 + (passo - 16) / 2
    for nome, aperto, tipo in voci:
        if tipo == "motion":
            stato, col = ("movimento", ORANGE) if aperto else ("tranquillo", GRIGIO)
        else:
            stato, col = ("aperta", ORANGE) if aperto else ("chiusa", GREEN)
        d.ellipse([14 * S, (y + 3) * S, 24 * S, (y + 13) * S], fill=col, outline=INK, width=S)
        nome = nome[:20]
        d.text((30 * S, (y + 8) * S), nome, font=_font(font, _testo_largo(d, nome, font, 15, FULL_W - 110)),
               fill=INK, anchor="lm")
        d.text(((FULL_W - 14) * S, (y + 8) * S), stato, font=_font(font, 14), fill=col, anchor="rm")
        y += passo
    return _done(img)


def schermata_numeri(titolo, voci, font):
    """Numeri grandi con l'etichetta (es. i passi di oggi). voci: [(testo, etichetta)], al massimo 4."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, titolo, font)
    voci = voci[:4]
    for c, (testo, etichetta) in zip(griglia(len(voci)), voci, strict=True):
        px = _testo_largo(d, testo, font, 30 if len(voci) == 1 else 22, c.w - 4)
        w_valore(d, c, testo, etichetta[:18], font, px=px)
    return _done(img)


URGENZA = {"info": BLUE, "avviso": YELLOW, "urgente": RED, "ok": GREEN}


def schermata_avviso(titolo, testo, livello, font):
    """Notifica a tutto cubo (CX): una fascia colorata col titolo e il testo grande sotto.
    livello: info | avviso | urgente | ok."""
    img, d = _canvas(FULL_W, FULL_H)
    d.rectangle([0, 0, FULL_W * S, 40 * S], fill=URGENZA.get(livello, YELLOW))
    titolo = (titolo or "Avviso")[:30]
    d.text((FULL_W / 2 * S, 20 * S), titolo, font=_font(font, _testo_largo(d, titolo, font, 18, FULL_W - 16)),
           fill=INK if livello in ("avviso", None) or livello not in URGENZA else WHITE, anchor="mm")
    spazio = FULL_H - 56
    for px in (20, 18, 16, 14, 12):
        righe = _righe(d, testo or "", font, px, FULL_W - 20, massimo=99)
        if len(righe) * (px + 6) <= spazio:
            break
    righe = _righe(d, testo or "", font, px, FULL_W - 20, massimo=max(1, int(spazio / (px + 6))))
    y = 40 + (FULL_H - 40 - len(righe) * (px + 6)) / 2
    for r in righe:
        d.text((FULL_W / 2 * S, y * S), r, font=_font(font, px), fill=INK, anchor="mt")
        y += px + 6
    return _done(img)


def colore_uso(p):
    """Per CPU, memoria e disco (al contrario delle batterie): verde sotto il 60%, giallo sotto l'85%,
    rosso sopra."""
    return GREEN if p < 60 else YELLOW if p < 85 else RED


def schermata_sistema(voci, carico, font):
    """Sistema di Home Assistant (3.5.1): voci [(nome, percento)] (CPU, memoria, disco), un anello
    ciascuna; carico: media del carico a 5 minuti o None."""
    img, d = _canvas(FULL_W, FULL_H)
    _titolo(d, "Home Assistant", font)
    voci = voci[:4]
    basso = 26 if carico is not None else 6
    for c, (nome, p) in zip(griglia(len(voci), basso=basso), voci, strict=True):
        w_anello(d, c, p, nome, font, colore=colore_uso(p))
    if carico is not None:
        d.text((FULL_W / 2 * S, (FULL_H - 6) * S), f"carico {carico:.2f}".replace(".", ","), font=_font(font, 14),
               fill=GRIGIO, anchor="mb")
    return _done(img)
