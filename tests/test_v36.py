"""La 3.6: rotte degli aerei da adsbdb (DL), argomenti bloccati ovunque (DM), diario non
ripetuto (DN), motivo vero degli scarti (DJ), foto cercate su Wikipedia (DG), saluti in
positivo (DH, DI), cache della cameretta senza fumetto (DK)."""
import io

from PIL import Image, ImageChops

import aerei
import alessio
import coinquilino
from test_app import DAY, FakeClaude, Resp

ATENE = {"municipality": "Athens", "latitude": 37.94, "longitude": 23.94}
ROMA = {"municipality": "Rome", "latitude": 41.80, "longitude": 12.25}


def _adsbdb(monkeypatch, origin, dest, code=200):
    def get(url, **kw):
        r = Resp({"response": {"flightroute": {"origin": origin, "destination": dest}}})
        r.status_code = code
        return r
    monkeypatch.setattr(aerei.requests, "get", get)
    aerei._ROUTES.clear()


def test_route_plausible_in_italian(monkeypatch):
    _adsbdb(monkeypatch, ATENE, ROMA)
    assert aerei.rotta("AEE652", 40.3, 18.2) == ("Atene", "Roma")     # sopra Lecce: sulla strada


def test_route_implausible_is_dropped_and_logged(monkeypatch):
    _adsbdb(monkeypatch, ATENE, ROMA)
    why = []
    assert aerei.rotta("AEE652", 52.0, 0.0, log=why.append) == (None, None)  # sopra Londra
    assert "non plausibile" in why[0]


def test_route_unknown_logged(monkeypatch):
    _adsbdb(monkeypatch, None, None, code=404)
    why = []
    assert aerei.rotta("XYZ1", 40.3, 18.2, log=why.append) == (None, None)
    assert why == ["XYZ1: rotta sconosciuta"]


def test_route_comes_first():
    a = {"flight": "AEE652", "type": "A20N", "alt_m": 11880, "route": ("Atene", "Roma")}
    assert aerei.descrivi(a) == "un volo Aegean da Atene a Roma, un Airbus A320neo a 11.880 metri"
    assert aerei.descrivi({"flight": "IAM12", "route": ("Pratica di Mare", "Lecce")}) == \
        "un volo dell'Aeronautica Militare da Pratica di Mare a Lecce"


def test_blocked_topic_everywhere_but_questions_answered(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.last_plane_talk = 0
    assert app._plane_ok()
    app.carattere.blocca("aerei")
    assert not app._plane_ok()
    asked = []
    app._coords = lambda: asked.append(1) or (40.0, 18.0)
    app.sources = list(app.sources) + ["aerei"]
    app._is_night = lambda: False
    app._planes({})
    assert not asked                                          # niente radar, niente diario
    p = app.carattere.prompt()
    assert "se qualcuno te ne chiede, rispondi" in p and "Non parlare mai" not in p


def test_diary_shown_once(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.mem["vetrina"] = {}
    app._vetrina_add({"tipo": "testo", "testo": "Dal mio diario di oggi: ciao.", "max_viste": 1})
    v = app._vetrina()
    v["voci"][0]["t"] -= 3600
    assert app._f_vetrina() == "Dal mio diario di oggi: ciao."
    v["voci"][0]["t"] -= 3600 if v["voci"] else 0
    assert app._f_vetrina() is None


def test_skip_reason_is_kept(make_app, cube, monkeypatch):
    FakeClaude(monkeypatch, "<frase>SALTA</frase>")
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app._argomento = lambda: ("notizia", None)
    app._listening = lambda: True
    app._write({"kind": "regista", "key": "x"})
    assert app._why_not == "niente da dire su notizia"


def test_wikipedia_search_when_disambiguation(make_app, cube, monkeypatch):
    buf = io.BytesIO()
    Image.new("RGB", (300, 200), (20, 20, 80)).save(buf, "PNG")
    asked = []

    def get(url, params=None, **kw):
        asked.append(url)
        if url.startswith(coinquilino.WIKI_SUMMARY):
            return Resp({"type": "disambiguation"})
        if url == coinquilino.WIKI_API:
            return Resp({"query": {"pages": [
                {"title": "Plutone", "index": 1, "pageprops": {"disambiguation": ""}},
                {"title": "Plutone (divinità)", "index": 2, "thumbnail": {"source": "https://x/dio.jpg"}},
                {"title": "Plutone (astronomia)", "index": 3, "thumbnail": {"source": "https://x/pianeta.jpg"}},
            ]}})
        r = Resp({})
        r.content = buf.getvalue()
        return r
    monkeypatch.setattr(coinquilino.requests, "get", get)
    app = make_app(dict(DAY, host=cube.host))
    img = app._wiki_foto("Plutone", "Plutone è un pianeta nano: l'astronomia lo ha declassato.")
    assert img is not None and asked[-1] == "https://x/pianeta.jpg"


def test_arrive_rules_are_positive():
    assert "Niente formule" not in coinquilino.OUTPUT_RULE
    assert "basta un saluto" in coinquilino.KIND_HINT["arrive"]


def test_room_cached_while_bubble_pages_change(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host))
    calls = []
    orig = alessio.render_base
    monkeypatch.setattr(alessio, "render_base", lambda *a, **k: calls.append(1) or orig(*a, **k))
    app.frame = 3
    a = app._render("happy", "day", None, "Prima pagina", True, True, None, False, {})
    b = app._render("happy", "day", None, "Seconda pagina", True, False, None, False, {})
    assert len(calls) == 1                                    # la stanza una volta sola
    ref = alessio.render("happy", "day", None, "Seconda pagina", 3, True, False, seed=7,
                         font_path=app.font_path)
    assert not ImageChops.difference(b, ref).getbbox() and a is not b
