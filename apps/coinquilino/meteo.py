"""
Il meteo dei giorni (2.0): i giorni passati e i prossimi da Open-Meteo, e le frasi di confronto.

Il grafico delle prossime 12 ore diceva cose ovvie (di giorno sale, di sera scende): quello che
serve sapere e' come cambia rispetto ai giorni prima (10/11). Open-Meteo da' i giorni
passati nella stessa chiamata (`past_days`): sono i valori del suo modello, non di una stazione,
ma per un confronto bastano.

  giorni(w)            la lista dei giorni ({data, tmin, tmax, pioggia, mm, codice, alba, tramonto})
  oggi_i(gg)           l'indice di oggi nella lista
  cielo(g)             sole | nuvole | pioggia | neve | temporale | nebbia
  confronti(gg, i)     frasi sui cambiamenti in arrivo, la piu' importante per prima
  rispetto_a_ieri(..)  per il buongiorno: oggi rispetto a ieri
  luce(gg, i)          ore di luce di oggi e differenza con una settimana fa

Solo libreria standard: si prova senza rete e senza AppDaemon.
"""

from datetime import date, datetime

GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
BREVI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]

DIFF_GIORNO = 3        # gradi di massima in piu' o in meno da un giorno all'altro: vale la pena dirlo
DIFF_IERI = 2          # al buongiorno basta meno
DIFF_SETTIMANA = 3     # media dei prossimi 3 giorni contro i 3 passati


def _get(d, key, i, default=None):
    v = d.get(key) or []
    return v[i] if i < len(v) and v[i] is not None else default


def _ora(x):
    try:
        return datetime.fromisoformat(str(x))
    except (TypeError, ValueError):
        return None


def giorni(w):
    """I giorni della risposta di Open-Meteo, in ordine. Senza "time" (vecchi dati) le date
    restano None e si conta da oggi."""
    d = (w or {}).get("daily") or {}
    n = len(d.get("temperature_2m_max") or [])
    out = []
    for i in range(n):
        t = _get(d, "time", i)
        out.append({
            "data": date.fromisoformat(t) if t else None,
            "tmin": _get(d, "temperature_2m_min", i), "tmax": _get(d, "temperature_2m_max", i),
            "pioggia": _get(d, "precipitation_probability_max", i, 0),
            "mm": _get(d, "precipitation_sum", i, 0), "codice": _get(d, "weather_code", i),
            "raffiche": _get(d, "wind_gusts_10m_max", i, 0),
            "alba": _ora(_get(d, "sunrise", i)), "tramonto": _ora(_get(d, "sunset", i)),
        })
    return out


def oggi_i(gg, oggi=None):
    oggi = oggi or date.today()
    for i, g in enumerate(gg):
        if g["data"] == oggi:
            return i
    return 0


def piovoso(g):
    return (g.get("mm") or 0) >= 1 or ((g.get("pioggia") or 0) >= 60 and (g.get("mm") or 0) > 0.2) \
        or cielo(g) in ("pioggia", "temporale")


def cielo(g):
    """Il cielo del giorno dal codice WMO (senza codice: dalla probabilita' di pioggia)."""
    c = g.get("codice")
    if c is None:
        return "pioggia" if (g.get("pioggia") or 0) >= 60 else "nuvole" if (g.get("pioggia") or 0) >= 30 else "sole"
    c = int(c)
    if c in (0, 1):
        return "sole"
    if c in (45, 48):
        return "nebbia"
    if 71 <= c <= 77 or c in (85, 86):
        return "neve"
    if c >= 95:
        return "temporale"
    if 51 <= c <= 67 or 80 <= c <= 82:
        return "pioggia"
    return "nuvole"


def _nome(gg, j, i):
    """Come chiamare il giorno j visto da oggi (i)."""
    k = j - i
    if k == 0:
        return "oggi"
    if k == 1:
        return "domani"
    if k == -1:
        return "ieri"
    d = gg[j]["data"]
    return GIORNI[d.weekday()] if d else f"tra {k} giorni"


def _gradi(x):
    x = abs(round(x))
    return "un grado" if x == 1 else f"{x} gradi"


def confronti(gg, i):
    """Frasi sui cambiamenti, la piu' importante per prima. Lista vuota se non cambia niente."""
    out = []
    if not gg or i + 1 >= len(gg) or gg[i]["tmax"] is None or gg[i + 1]["tmax"] is None:
        return out
    oggi, dom = gg[i], gg[i + 1]
    # pioggia che arriva o che finisce
    passati = [g for g in gg[max(0, i - 3):i + 1]]
    bagnati = 0
    for g in reversed(passati):
        if not piovoso(g):
            break
        bagnati += 1
    if bagnati >= 2 and not piovoso(dom):
        out.append(f"Da domani torna il sereno, dopo {bagnati} giorni di pioggia.")
    elif not piovoso(oggi):
        prossimo = next((j for j in range(i + 1, min(len(gg), i + 4)) if piovoso(gg[j])), None)
        if prossimo is not None and not any(piovoso(g) for g in passati):
            out.append(f"Dopo giorni asciutti, pioggia in arrivo {_nome(gg, prossimo, i)}.")
    # temperatura: domani rispetto a oggi
    dt = dom["tmax"] - oggi["tmax"]
    if abs(dt) >= DIFF_GIORNO:
        out.append(f"Domani {_gradi(dt)} {'in meno' if dt < 0 else 'in più'} di oggi: "
                   f"massima {dom['tmax']:.0f}.")
    # la tendenza: i prossimi 3 giorni contro i 3 passati
    prima = [g["tmax"] for g in gg[max(0, i - 3):i] if g["tmax"] is not None]
    dopo = [g["tmax"] for g in gg[i + 1:i + 4] if g["tmax"] is not None]
    if len(prima) >= 2 and len(dopo) >= 2:
        dm = sum(dopo) / len(dopo) - sum(prima) / len(prima)
        if abs(dm) >= DIFF_SETTIMANA and not (abs(dt) >= DIFF_GIORNO and (dt > 0) == (dm > 0)):
            out.append(f"Nei prossimi giorni {'più freddo' if dm < 0 else 'più caldo'}: massime "
                       f"intorno ai {sum(dopo) / len(dopo):.0f} gradi, contro i "
                       f"{sum(prima) / len(prima):.0f} degli ultimi giorni.")
    return out


def rispetto_a_ieri(gg, i):
    """Per il buongiorno: oggi rispetto a ieri ("" se e' uguale)."""
    if i < 1 or i >= len(gg) or gg[i]["tmax"] is None or gg[i - 1]["tmax"] is None:
        return ""
    dt = gg[i]["tmax"] - gg[i - 1]["tmax"]
    if abs(dt) < DIFF_IERI:
        return ""
    return f"Oggi {_gradi(dt)} {'più freddo' if dt < 0 else 'più caldo'} di ieri."


def luce(gg, i):
    """(minuti di luce oggi, differenza in minuti con 7 giorni fa) oppure None."""
    def m(g):
        if not g.get("alba") or not g.get("tramonto"):
            return None
        return (g["tramonto"] - g["alba"]).total_seconds() / 60
    if i >= len(gg):
        return None
    oggi = m(gg[i])
    if oggi is None:
        return None
    prima = m(gg[i - 7]) if i >= 7 else None
    return round(oggi), (round(oggi - prima) if prima is not None else None)
