"""Le correzioni della 1.2 (dal log del 27/10/2026)."""
from datetime import date, datetime, timedelta

import aerei
import coinquilino
from conftest import STATES
from test_app import DAY, FakeClaude

USAGE = '<frase>Ciao!</frase>'


def lines(app, action):
    return [m for _, m in app.logs if m.startswith(action)]


# ------------------------------------------------------------------ uscite
def test_leave_is_told_to_who_stays_and_is_free(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch)
    states = dict(STATES, **{"person.anna": {"state": "not_home", "attributes": {"friendly_name": "Anna"}}})
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"), states=states)   # Mario e' in casa
    app._still_away({"entity": "person.anna", "name": "Anna"})
    app._say_leaves({})
    app._speak({})
    assert app.msg["text"] == "Anna è fuori casa."
    assert not fake.calls                                          # niente Claude per le uscite
    assert any("SAY    free event   person.leave" in m for m in lines(app, "SAY"))


def test_leave_with_empty_house_is_only_remembered(make_app, cube):
    states = {k: v for k, v in STATES.items() if not k.startswith("person.")}
    states["person.anna"] = {"state": "not_home", "attributes": {"friendly_name": "Anna"}}
    app = make_app(dict(DAY, host=cube.host), states=states)
    app._still_away({"entity": "person.anna", "name": "Anna"})
    assert not app.queue
    assert any("person.leave" in m and "casa vuota" in m for m in lines(app, "SKIP"))
    assert "è uscito di casa: Anna" in app.mem["giorni"][date.today().isoformat()]["eventi"][-1]


# ------------------------------------------------------------------ riavvii
def test_morning_and_last_lines_survive_a_restart(make_app, cube):
    args = dict(DAY, host=cube.host)
    app = make_app(args)
    app._told("morning", date.today().isoformat())
    app._say_now("Q8 ha esteso il limite ai carburanti", "regista")
    again = make_app(args)
    assert again.morning_day == date.today()
    assert "Q8 ha esteso il limite ai carburanti" in again.said_recent


# ------------------------------------------------------------------ aerei
def test_ground_transponders_are_ignored(make_app, cube, monkeypatch):
    planes = [{"hex": "3007a4", "flight": "", "reg": None, "type": None, "alt_m": 8, "kmh": None,
               "lat": 44.49, "lon": 11.34, "km": 0.5},
              {"hex": "440735", "flight": "EZY1", "reg": None, "type": "A319", "alt_m": 10676, "kmh": 800,
               "lat": 44.50, "lon": 11.35, "km": 1.5}]
    monkeypatch.setattr(aerei, "vicini", lambda lat, lon, r: [dict(p) for p in planes])
    monkeypatch.setattr(aerei, "rotta", lambda *a: (None, None))
    app = make_app(dict(DAY, host=cube.host))
    app._planes({})
    assert [p["hex"] for p in app.planes] == ["440735"]
    assert [f["key"] for f in app.queue] == ["440735"]
    assert any("quota 8 m" in m for m in lines(app, "SKIP"))


def test_new_plane_defaults(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    assert (app.plane_radius, app.overhead_km, app.plane_min_m) == (15, 3, 150)


# ------------------------------------------------------------------ disegni e coda
def test_drawing_grid_is_aligned_not_thrown_away():
    rows = coinquilino.Coinquilino._grid("..GG..\n.OOOO.\nOOKKOO\nOOOOOOO\n.OOOO\n..OO..\n")
    assert rows and {len(r) for r in rows} == {6}
    assert coinquilino.Coinquilino._grid("GG\nOOOOOOOOOO\nOO\nOO\nOO\nOO") is None   # troppo storto
    assert coinquilino.Coinquilino._grid("..GG..\n.XXXX.\n" * 4) is None            # colori sconosciuti


def test_drawing_with_unclosed_tag_is_kept(make_app, cube, monkeypatch):
    FakeClaude(monkeypatch, "<titolo>Una zucca!</titolo>\n<disegno>\n" + ".OOOOOO.\n" * 8)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    title, card = app._ask_drawing()
    assert title == "Una zucca!" and card is not None


def test_only_one_director_turn_in_queue(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app.add_fact("regista", key="202610270734")
    app.add_fact("regista", key="202610270759")
    assert [f["kind"] for f in app.queue] == ["regista"]


def test_leave_and_morning_go_before_the_director(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.add_fact("regista", key="1")
    app.add_fact("morning", tmin=11, tmax=18, rain=0, key="m")
    app.add_fact("leave", name="Anna", key="person.anna")
    assert [f["kind"] for f in app.queue] == ["morning", "leave", "regista"]   # urgenti in ordine di arrivo


# ------------------------------------------------------------------ chiacchiere
def test_moto_only_on_moto_days(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, moto_days=[(datetime.now().weekday() + 3) % 7]))
    app.forecast = {"daily": {"temperature_2m_min": [11, 11], "temperature_2m_max": [20, 20],
                              "precipitation_probability_max": [0, 0]}}
    assert "moto" not in app._f_previsioni()
    app.moto_days = [datetime.now().weekday(), (datetime.now() + timedelta(days=1)).weekday()]
    assert "moto" in app._f_previsioni()


def test_indoor_temperature_is_an_average_with_sensors(make_app, cube):
    states = dict(STATES, **{
        "climate.condizionatore": {"state": "cool", "attributes": {"current_temperature": 23}},
        "climate.tado": {"state": "heat", "attributes": {"current_temperature": 22}},
        "sensor.shelly_ht_temperatura": {"state": "21.5", "attributes": {"device_class": "temperature"}},
        "sensor.frigo": {"state": "4", "attributes": {"device_class": "temperature"}}})
    app = make_app(dict(DAY, host=cube.host, indoor_temperature=[
        "climate.condizionatore", "climate.tado", "sensor.shelly_ht_temperatura"]), states=states)
    assert app._indoor_temp() == (22.166666666666668, 21.5, 23)
    assert any("In casa ci sono 22 gradi" in (app._f_casa() or "") for _ in range(20))
    plain = make_app(dict(DAY, host=cube.host), states=states)            # senza lista: solo i climate
    assert plain._indoor_temp() == (22.5, 22, 23)


def test_claude_usage_chatter_only_when_worth_it(make_app, cube):
    states = dict(STATES, **{"sensor.claude_usage_s": {"state": "0", "attributes": {"kind": "session"}},
                             "sensor.claude_usage_w": {"state": "65", "attributes": {"kind": "weekly_all"}}})
    app = make_app(dict(DAY, host=cube.host), states=states)
    assert app._f_claude() is None and app._f_grafico_claude() is None
    app.states["sensor.claude_usage_s"] = {"state": "55", "attributes": {"kind": "session"}}
    assert "55%" in app._f_claude()


# ------------------------------------------------------------------ log e voce
def test_log_shows_cost_and_real_tokens(make_app, cube, monkeypatch):
    FakeClaude(monkeypatch, USAGE)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", claude_max_per_hour=1))
    app.add_fact("arrive", name="Anna", key="person.anna")
    app._speak({})
    claude = lines(app, "CLAUDE")
    assert claude and "person.arrive" in claude[0] and "1834+62 token | oggi 1/150, ultima ora 1/1" in claude[0]
    assert any(m.startswith("SAY    paid event   person.arrive") for m in lines(app, "SAY"))
    app.last_said, app.msg = 0, None
    app.add_fact("arrive", name="Mario", key="person.mario")
    app._speak({})                                                # tetto raggiunto: frase fissa
    assert any(m.startswith("SAY    free (fallback) event   person.arrive") for m in lines(app, "SAY"))


def test_voice_kinds_accept_new_and_old_names(make_app, cube):
    new = make_app(dict(DAY, host=cube.host, voice_kinds=["chat.reply", "plane.overhead"]))
    old = make_app(dict(DAY, host=cube.host, voice_kinds=["chat", "plane"]))
    assert new.voice_kinds == old.voice_kinds == {"chat", "plane"}
