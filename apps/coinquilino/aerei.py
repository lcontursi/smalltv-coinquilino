"""
Aerei sopra casa, dai dati ADS-B pubblici e gratuiti.

- posizioni: adsb.lol (v2) e, se non risponde, adsb.fi (v3), stesso formato
  ("ac": [{hex, flight, r, t, alt_baro, gs, track, lat, lon}, ...])
- rotta (3.6, DL): adsbdb.com /v0/callsign/<callsign> -> aeroporti di partenza e arrivo, con un
  controllo di plausibilita' (l'aereo deve stare grosso modo fra le due citta': un callsign
  riusato puo' avere una rotta vecchia). Il vecchio servizio di adsb.lol risponde 500.

Niente chiavi, niente account. Limite: circa 1 richiesta al secondo; il
coinquilino ne fa una al minuto.
"""
import math
import time

import requests

UA = {"User-Agent": "coinquilino-smalltv/1.0 (Home Assistant AppDaemon)"}

AIRLINES = {
    "RYR": "Ryanair", "RUK": "Ryanair", "EXS": "Jet2", "EZY": "easyJet", "EJU": "easyJet",
    "EZS": "easyJet", "ITY": "ITA Airways", "AZA": "ITA Airways", "WZZ": "Wizz Air",
    "WMT": "Wizz Air", "WUK": "Wizz Air", "VLG": "Vueling", "VOE": "Volotea", "DLH": "Lufthansa",
    "EWG": "Eurowings", "AFR": "Air France", "KLM": "KLM", "BAW": "British Airways",
    "AEE": "Aegean", "THY": "Turkish Airlines", "PGT": "Pegasus", "SWR": "Swiss",
    "AUA": "Austrian", "TAP": "TAP", "IBE": "Iberia", "UAE": "Emirates", "QTR": "Qatar Airways",
    "ETD": "Etihad", "ELY": "El Al", "MSR": "EgyptAir", "TVS": "Smartwings", "NOZ": "Norwegian",
    "NAX": "Norwegian", "SXS": "SunExpress", "CND": "Corendon", "TOM": "TUI", "TUI": "TUI",
    "NOS": "Neos", "AEY": "Air Italy", "DAH": "Air Algérie", "RAM": "Royal Air Maroc",
    "TAR": "Tunisair", "FDX": "FedEx", "UPS": "UPS", "DHK": "DHL", "BCS": "DHL",
    "IAM": "l'Aeronautica Militare", "CFC": "un volo militare canadese", "RCH": "l'aviazione USA",
    "SAM": "un volo di Stato", "GAF": "l'aviazione tedesca",
}

TYPES = {
    "B738": "un Boeing 737", "B737": "un Boeing 737", "B739": "un Boeing 737",
    "B38M": "un Boeing 737 MAX", "B39M": "un Boeing 737 MAX", "B752": "un Boeing 757",
    "B763": "un Boeing 767", "B772": "un Boeing 777", "B77W": "un Boeing 777",
    "B788": "un Boeing 787", "B789": "un Boeing 787", "B744": "un Boeing 747", "B748": "un Boeing 747",
    "A319": "un Airbus A319", "A320": "un Airbus A320", "A20N": "un Airbus A320neo",
    "A321": "un Airbus A321", "A21N": "un Airbus A321neo", "A332": "un Airbus A330",
    "A333": "un Airbus A330", "A339": "un Airbus A330neo", "A359": "un Airbus A350",
    "A35K": "un Airbus A350", "A388": "un Airbus A380", "BCS3": "un Airbus A220",
    "AT72": "un ATR 72 a eliche", "AT75": "un ATR 72 a eliche", "AT76": "un ATR 72 a eliche",
    "DH8D": "un Dash 8 a eliche", "E190": "un Embraer", "E195": "un Embraer",
    "E290": "un Embraer", "E295": "un Embraer", "CRJ9": "un Bombardier CRJ",
    "C130": "un Hercules militare", "C30J": "un Hercules militare", "EUFI": "un Eurofighter",
    "F35": "un F-35", "H500": "un elicottero", "A139": "un elicottero", "EC35": "un elicottero",
    "EC45": "un elicottero", "AW39": "un elicottero",
}


def _km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def vicini(lat, lon, raggio_km=25):
    """Aerei entro raggio_km, dal piu' vicino. Ogni aereo e' un dict semplice."""
    nm = max(1, int(raggio_km / 1.852) + 1)
    urls = [f"https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{nm}",
            f"https://opendata.adsb.fi/api/v3/lat/{lat}/lon/{lon}/dist/{nm}"]
    data, err = None, None
    for u in urls:
        try:
            r = requests.get(u, headers=UA, timeout=10)
            r.raise_for_status()
            data = r.json()
            break
        except Exception as e:          # prova la fonte successiva
            err = e
    if data is None:
        raise RuntimeError(f"nessuna fonte ADS-B: {err}")
    out = []
    for a in data.get("ac") or data.get("aircraft") or []:
        if a.get("lat") is None or a.get("lon") is None:
            continue
        alt = a.get("alt_baro")
        if alt == "ground":
            continue
        try:
            alt_m = round(float(alt) * 0.3048) if alt is not None else None
        except (TypeError, ValueError):
            alt_m = None
        out.append({
            "hex": a.get("hex"),
            "flight": (a.get("flight") or "").strip(),
            "reg": a.get("r"),
            "type": a.get("t"),
            "alt_m": alt_m,
            "kmh": round(float(a["gs"]) * 1.852) if a.get("gs") is not None else None,
            "lat": a["lat"], "lon": a["lon"],
            "km": round(_km(lat, lon, a["lat"], a["lon"]), 1),
        })
    out.sort(key=lambda x: x["km"])
    return [a for a in out if a["km"] <= raggio_km]


_ROUTES = {}

# nomi italiani delle citta' piu' comuni (adsbdb le da' in inglese)
CITTA = {
    "Rome": "Roma", "Milan": "Milano", "Naples": "Napoli", "Turin": "Torino", "Venice": "Venezia",
    "Florence": "Firenze", "Genoa": "Genova", "Bergamo": "Bergamo", "Bologna": "Bologna",
    "Athens": "Atene", "London": "Londra", "Paris": "Parigi", "Munich": "Monaco di Baviera",
    "Brussels": "Bruxelles", "Lisbon": "Lisbona", "Warsaw": "Varsavia", "Prague": "Praga",
    "Vienna": "Vienna", "Geneva": "Ginevra", "Zurich": "Zurigo", "Cologne": "Colonia",
    "Istanbul": "Istanbul", "Cairo": "Il Cairo", "Moscow": "Mosca", "Bucharest": "Bucarest",
    "Copenhagen": "Copenaghen", "Stockholm": "Stoccolma", "Seville": "Siviglia",
    "Thessaloniki": "Salonicco", "Heraklion": "Candia", "Tirana": "Tirana", "Belgrade": "Belgrado",
    "Sofia": "Sofia", "Nicosia": "Nicosia", "Larnaca": "Larnaca", "Tel Aviv": "Tel Aviv",
    "Dubai": "Dubai", "Doha": "Doha", "Frankfurt": "Francoforte", "Frankfurt am Main": "Francoforte",
    "Dusseldorf": "Düsseldorf", "Düsseldorf": "Düsseldorf", "Marseille": "Marsiglia",
    "Nice": "Nizza", "Barcelona": "Barcellona", "Catania": "Catania", "Palermo": "Palermo",
    "Bari": "Bari", "Brindisi": "Brindisi", "Cagliari": "Cagliari", "Pisa": "Pisa",
    "Verona": "Verona", "Treviso": "Treviso", "Lamezia Terme": "Lamezia Terme",
}


def _citta(ap):
    nome = (ap.get("municipality") or ap.get("name") or ap.get("iata_code") or "").strip()
    return CITTA.get(nome, nome)


def plausibile(lat, lon, o, d):
    """L'aereo sta grosso modo sulla strada fra o e d? Ellisse: la somma delle distanze dai due
    aeroporti non supera di molto la distanza fra loro (25% + 150 km di margine)."""
    tot = _km(o["latitude"], o["longitude"], d["latitude"], d["longitude"])
    via = _km(lat, lon, o["latitude"], o["longitude"]) + _km(lat, lon, d["latitude"], d["longitude"])
    return via <= tot * 1.25 + 150


def rotta(callsign, lat, lon, log=None):
    """(partenza, arrivo) come nomi di citta', oppure (None, None). log(motivo) se non c'e'."""
    cs = (callsign or "").strip().upper()
    if not cs:
        return None, None
    hit = _ROUTES.get(cs)
    if hit and time.time() - hit[0] < 6 * 3600:
        return hit[1]
    res, why = (None, None), None
    try:
        r = requests.get(f"https://api.adsbdb.com/v0/callsign/{cs}", headers=UA, timeout=10)
        if r.status_code == 404:
            why = "rotta sconosciuta"
        else:
            r.raise_for_status()
            fr = ((r.json() or {}).get("response") or {})
            fr = fr.get("flightroute") if isinstance(fr, dict) else None
            o, d = (fr or {}).get("origin") or {}, (fr or {}).get("destination") or {}
            if not (o and d):
                why = "rotta sconosciuta"
            elif not plausibile(lat, lon, o, d):
                why = f"rotta non plausibile ({_citta(o)}-{_citta(d)})"
            else:
                res = (_citta(o), _citta(d))
    except Exception as e:
        why = f"rotta non disponibile: {e}"
    if why and log:
        log(f"{cs}: {why}")
    _ROUTES[cs] = (time.time(), res)
    return res


def compagnia(callsign):
    cs = (callsign or "").upper()
    return AIRLINES.get(cs[:3]) if len(cs) > 3 and cs[:3].isalpha() else None


def tipo(t):
    return TYPES.get((t or "").upper())


def descrivi(a, route=None):
    """Frase semplice, senza Claude. Con la rotta (3.6, DL) viene prima la rotta:
    'un volo Ryanair da Brindisi a Bergamo, un Boeing 737 a 3.200 metri'; senza:
    'un Boeing 737 Ryanair a 3.200 metri'."""
    da, a_ = route or a.get("route") or (None, None)
    comp = compagnia(a.get("flight"))
    tp = tipo(a.get("type"))
    alt = f"a {a['alt_m']:,} metri".replace(",", ".") if a.get("alt_m") else ""
    if da and a_:
        chi = ("un volo" + (f" {comp}" if comp and not comp.startswith(("l'", "un ")) else "")
               + (f" del{comp}" if comp and comp.startswith("l'") else ""))
        resto = " ".join(x for x in (tp, alt) if x)
        return f"{chi} da {da} a {a_}" + (f", {resto}" if resto else "")
    parti = []
    if comp and tp:
        if comp.startswith("l'"):
            parti.append(f"{tp} del{comp}")            # "dell'Aeronautica Militare"
        elif comp.startswith("un "):
            parti.append(f"{tp}, {comp}")
        else:
            parti.append(f"{tp} {comp}")
    elif comp:
        parti.append(f"un aereo {comp}")
    elif tp:
        parti.append(tp)
    else:
        parti.append("un aereo")
    if alt:
        parti.append(alt)
    return " ".join(parti)
