"""La 2.1.1 (CH, CE): lavagnette e schermate restano finche' non arriva altro, a cubo vuoto la
vetrina torna dopo pochi minuti, in vetrina il diario di oggi."""
import time

import coinquilino
from test_app import DAY


def test_card_stays_until_something_else(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, show_minutes=20, card_seconds=40))
    app.msg = {"pages": ["Il meteo della settimana."], "t0": time.time() - 10 * 60, "kind": "filler",
               "card": object()}
    assert app._bubble()[0] == "Il meteo della settimana."          # dopo 10 minuti c'e' ancora
    assert not app._talking()                                        # ma un'altra cosa puo' arrivare


def test_empty_cube_gets_the_next_thing_sooner(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, talk_every_minutes=6))
    app.msg = app.photo = None
    assert app._turn_secs() == 60
    app.msg = {"pages": ["Ciao."], "t0": time.time(), "kind": "filler"}
    assert app._turn_secs() == 360


def test_empty_cube_tries_the_showcase_first(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host))
    app.mem["curiosita"] = ["le api ballano."]
    app._f_fatto()
    for x in app._vetrina()["voci"]:
        x["t"] -= 3600
    app.msg = app.photo = None
    app.last_said = app.last_filler = 0
    monkeypatch.setattr(app, "_is_night", lambda h=None: False)
    monkeypatch.setattr(app, "_house_empty", lambda: False)
    app._filler({})
    assert app.msg and app.msg["text"].startswith("Curiosità di oggi")
    assert coinquilino.CHATTER_DAY["vetrina"] >= 99


def test_showcase_uses_todays_diary(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._vetrina()["voci"].append({"tipo": "testo", "testo": "Dal mio diario di ieri: vecchio.",
                                   "t": 0, "viste": 0})
    app.queue.append({"kind": "diario", "at": time.time(), "prio": 1})
    app.last_said = 0
    app._write = lambda fact: ("Caro diario, oggi sole.", "paid")
    app._speak({})
    testi = [x.get("testo") for x in app._vetrina()["voci"]]
    assert "Dal mio diario di oggi: Caro diario, oggi sole." in testi
    assert not any("di ieri" in (t or "") for t in testi)
