"""La 2.2.1 (CI): i ricordi notturni sanno l'eta' di oggi e lasciano fuori il superfluo."""
import coinquilino
from test_v14 import FakeBatch, night_app


def test_night_memory_rules(make_app, cube, monkeypatch):
    FakeBatch(monkeypatch)
    app = night_app(make_app, cube, monkeypatch)
    monkeypatch.setattr(coinquilino.Coinquilino, "anni", property(lambda self: 10))
    app._chat_reply("la moto è dal meccanico")
    reqs = {r["kind"]: r["params"]["messages"][0]["content"] for r in app._night_requests()}
    t = reqs["ricordi"]
    assert "ha 10 anni" in t and "ciuccio" in t
    assert "uscite, rientri e orari delle persone" in t and "nomi di dispositivi" in t
    assert "descrizioni di te o di cosa sai fare" in t and "sul programma" in t


def test_cost_sensor_published_with_the_state(make_app, cube):
    from test_app import DAY
    app = make_app(dict(DAY, host=cube.host))
    app._publish_state()
    assert "sensor.coinquilino_costo_api" in app.published


def test_showcase_keeps_turning_on_an_empty_cube(make_app, cube):
    """2.2.3 (CL): a cubo vuoto la vetrina riprende una voce vista 7 minuti fa."""
    import time

    from test_app import DAY
    app = make_app(dict(DAY, host=cube.host))
    app.mem.pop("vetrina", None)
    app._vetrina_add({"tipo": "testo", "testo": "Domani 24 gradi e sole: giornata da moto."})
    for x in app._vetrina()["voci"]:
        x["t"] = time.time() - 7 * 60
    app.msg = {"pages": ["x"], "t0": time.time(), "kind": "filler"}
    assert app._f_vetrina() is None                                  # c'e' gia' qualcosa: aspetta
    app.msg = app.photo = None
    assert app._f_vetrina() == "Domani 24 gradi e sole: giornata da moto."


def test_director_lines_join_the_showcase_unless_stale(make_app, cube):
    import coinquilino
    assert coinquilino.Coinquilino._showcase_ok("Domani 24 gradi, pioggia al 5 per cento.")
    assert not coinquilino.Coinquilino._showcase_ok("Fuori ci sono 17 gradi e in casa 21.")
    assert not coinquilino.Coinquilino._showcase_ok("Il consumo di Claude è al 12 per cento.")
