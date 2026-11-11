"""
Feste e ricorrenze per il coinquilino.

festa_di(data, compleanni, patrono) -> (chiave, descrizione) oppure (None, None)

chiavi: compleanno, capodanno, pasqua, halloween, natale, patrono
compleanni: {"MM-DD": "Nome", ...} (dalle impostazioni)
patrono:    {"from": "MM-DD", "to": "MM-DD", "name": "la festa di ..."} (facoltativo)
"""
from datetime import date, timedelta


def pasqua(anno):
    """Domenica di Pasqua (algoritmo di Gauss/Meeus, calendario gregoriano)."""
    a, b, c = anno % 19, anno // 100, anno % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mese = (h + l - 7 * m + 114) // 31
    giorno = (h + l - 7 * m + 114) % 31 + 1
    return date(anno, mese, giorno)


def festa_di(oggi, compleanni=None, patrono=None):
    md = oggi.strftime("%m-%d")
    for k, nome in (compleanni or {}).items():
        if str(k) == md:
            return "compleanno", f"il compleanno di {nome}"
    if md in ("12-31", "01-01"):
        return "capodanno", "Capodanno"
    p = pasqua(oggi.year)
    if p - timedelta(days=1) <= oggi <= p + timedelta(days=1):
        return "pasqua", "Pasqua" if oggi == p else ("Pasquetta" if oggi > p else "la vigilia di Pasqua")
    if ("10-24" <= md <= "10-31") or md == "11-01":
        return "halloween", {"10-31": "Halloween", "11-01": "Ognissanti, il giorno dopo Halloween"}.get(
            md, "la settimana di Halloween")
    if md >= "12-08" or md <= "01-06":
        nomi = {"12-24": "la Vigilia di Natale", "12-25": "Natale", "12-26": "Santo Stefano",
                "01-06": "la Befana"}
        return "natale", nomi.get(md, "il periodo di Natale")
    if patrono and str(patrono.get("from", "")) <= md <= str(patrono.get("to", patrono.get("from", ""))):
        return "patrono", patrono.get("name", "la festa del santo patrono")
    return None, None
