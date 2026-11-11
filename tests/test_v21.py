"""La 2.1: niente ripetizioni (meteo di domani, aggiornamenti, temperature), vetrina del giorno,
tetti spalmati nella giornata, foto a giro con un tetto, uscite insieme, director senza coda."""
import time
from datetime import date, timedelta

import coinquilino
from conftest import STATES
from test_app import DAY, FakeClaude
from test_v20 import week


def at_hour(monkeypatch, h):
    class Fixed(coinquilino.datetime):
        @classmethod
        def now(cls, tz=None):
            return coinquilino.datetime.combine(date.today(), coinquilino.datetime.min.time()).replace(hour=h)
    monkeypatch.setattr(coinquilino, "datetime", Fixed)


# ------------------------------------------------------------------ ripetizioni (BM, CA, BO)
def test_tomorrow_weather_said_once(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host))
    app.forecast = week([20, 21, 20, 19, 21, 20, 19, 19, 14, 13, 14])
    at_hour(monkeypatch, 16)
    app._say_now("Domani fa 14 gradi, cinque in meno di oggi.", "regista", cost="paid")
    assert app._tema_detto("meteo di domani")
    app.add_fact("forecast_change", text="Domani 5 gradi in meno di oggi: massima 14.", key="x")
    app.msg = None
    app._speak({})
    assert not app.queue and app.msg is None                       # l'avviso tace
    assert app._f_previsioni() is None                              # la chiacchiera pure
    text, card = app._f_grafico_meteo()                             # la lavagnetta resta, senza domani
    assert "omani" not in text and card is not None
    ctx = " ".join(app._context(full=True))
    assert "Argomenti già detti oggi" in ctx and "meteo di domani" in ctx


def test_updates_not_repeated_by_home_chatter(make_app, cube):
    states = dict(STATES, **{"update.core": {"state": "on", "attributes": {"title": "Core"}}})
    app = make_app(dict(DAY, host=cube.host), states=states)
    app._say_now("In Home Assistant c'è un aggiornamento da installare: Core.", "update")
    for _ in range(20):
        assert "aggiornament" not in app._f_casa()


# ------------------------------------------------------------------ temperature (BT)
def test_temperatures_only_when_changed_or_asked(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    assert any("Meteo a" in x for x in app._context())
    app._say_now("Fuori ci sono 21 gradi.", "regista", cost="paid")
    assert not any("Meteo a" in x for x in app._context())
    assert app._f_meteo() is None
    assert any("Meteo a" in x for x in app._context(chat_text="che tempo fa?"))
    app.states["weather.casa"] = {"state": "sunny", "attributes": {"temperature": 15}}   # 6 gradi in meno
    assert any("Meteo a" in x for x in app._context())


def test_claude_usage_only_when_it_matters(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host))
    monkeypatch.setattr(app, "_claude_session", lambda: 12.0)
    assert not any("Consumo di Claude" in x for x in app._context(full=True))
    monkeypatch.setattr(app, "_claude_session", lambda: 80.0)
    assert any("Consumo di Claude" in x for x in app._context(full=True))


# ------------------------------------------------------------------ vetrina (BS)
def test_showcase_brings_back_today_things(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.mem["curiosita"] = ["le api ballano per indicare i fiori."]
    assert "api ballano" in app._f_fatto()
    assert app._f_vetrina() is None                                  # appena detta: non subito
    for x in app._vetrina()["voci"]:
        x["t"] -= 3600
    assert app._f_vetrina() == "Curiosità di oggi: le api ballano per indicare i fiori."


def test_showcase_keeps_drawing_and_yesterday_diary(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    ieri = (date.today() - timedelta(days=1)).isoformat()
    app.mem["giorni"][ieri] = {"eventi": [], "diario": "Caro diario, oggi pioggia."}
    app.mem.pop("vetrina", None)
    app.drawing_kept = ("Un gatto", [".KK.", "KWWK"] * 4)
    app._say_now("Un gatto", "disegno", card=object(), cost="paid")
    voci = app._vetrina()["voci"]
    assert voci[0]["testo"] == "Dal mio diario di ieri: Caro diario, oggi pioggia."
    assert voci[-1]["tipo"] == "disegno"
    for x in voci:
        x["t"] -= 3600
    first = app._f_vetrina()
    second = app._f_vetrina()
    got = [first if isinstance(first, str) else first[0], second if isinstance(second, str) else second[0]]
    assert "Il disegno di oggi: Un gatto" in got and any("diario" in g for g in got)


def test_showcase_is_in_the_chatter_rotation(make_app, cube):
    make_app(dict(DAY, host=cube.host))
    assert coinquilino.CHATTER_DAY["vetrina"] >= 20 and "vetrina" in coinquilino.CHATTER_EVERY


# ------------------------------------------------------------------ tetti nella giornata (BV, BP)
def test_daily_caps_spread_over_the_day(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host, night_start=23, night_end=7))
    at_hour(monkeypatch, 8)
    morning = app._day_cap("notizia")
    at_hour(monkeypatch, 15)
    afternoon = app._day_cap("notizia")
    at_hour(monkeypatch, 22)
    assert 1 <= morning < afternoon < app._day_cap("notizia") == coinquilino.CHATTER_DAY["notizia"] == 5


# ------------------------------------------------------------------ foto (BU)
def test_each_photo_at_most_n_times_a_day(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host, photo_day_max=2))
    shown = []

    class Album:
        def foto(self):
            return ["a.png", "b.png"]

        def prossima(self):
            n = "a.png" if len(shown) % 2 == 0 else "b.png"
            return n, None

        def sincronizza(self):
            return [], []
    app.album = Album()
    monkeypatch.setattr(app, "_photo_import", lambda: [])
    monkeypatch.setattr(app, "_album_changed", lambda: False)
    monkeypatch.setattr(app, "_is_night", lambda h=None: False)
    monkeypatch.setattr(app, "_photo_show", lambda img, n: shown.append(n))
    for _ in range(8):
        app.last_photo, app.msg, app.photo = 0, None, None
        app._photo_turn({})
    assert sorted(shown) == ["a.png", "a.png", "b.png", "b.png"]


# ------------------------------------------------------------------ persone (BX, BY)
def test_leaving_together_is_one_line(make_app, cube):
    states = dict(STATES, **{"person.luisa": {"state": "not_home", "attributes": {"friendly_name": "Luisa"}}})
    app = make_app(dict(DAY, host=cube.host), states=states)
    app._still_away({"entity": "person.anna", "name": "Anna"})
    app._still_away({"entity": "person.luisa", "name": "Luisa"})
    app._say_leaves({})
    assert [f["name"] for f in app.queue] == ["Anna e Luisa"]
    app._speak({})
    assert app.msg["text"] == "Fuori casa: Anna e Luisa."


def test_fallback_plural_and_reason_logged(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    text, _ = app._write({"kind": "arrive", "name": "Anna e Mario", "names": ["Anna", "Mario"]})
    assert text == "Ciao Anna e Mario, eccovi a casa."


def test_arrival_calls_claude_even_if_presence_lags(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch, "<frase>Ciao Anna, piove da un'ora.</frase>")
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", presence=["person.anna"]))
    text, cost = app._write({"kind": "arrive", "name": "Anna", "key": "person.anna"})
    assert cost == "paid" and fake.calls


# ------------------------------------------------------------------ director e frasi (BN, BQ, BR, BZ)
def test_director_waits_for_a_free_slot_instead_of_queueing(make_app, cube, monkeypatch):
    FakeClaude(monkeypatch)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app.last_random, app.last_said = 0, time.time()
    app._random({})
    assert not app.queue                                            # avrebbe aspettato 15 minuti
    app.last_said = 0
    app._random({})
    assert app.queue


def test_reply_starts_with_a_capital_and_no_invented_drawings(make_app, cube, monkeypatch):
    FakeClaude(monkeypatch, "<frase>sto bene, grazie.</frase>")
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    text, _ = app._claude(["x"], [], "chat")
    assert text == "Sto bene, grazie."
    assert "non inventare cose che avresti fatto" in app.persona


def test_plane_lines_carry_information(make_app, cube):
    assert not any("Brumm" in x or "Guarda, guarda" in x for x in coinquilino.PLANE_LINES)
    app = make_app(dict(DAY, host=cube.host))
    app.planes = [{"km": 7.0, "alt_m": 9000, "kmh": 800, "hex": "a", "lat": 44.5, "lon": 11.3, "dx": 3.0, "dy": 6.0,
                   "tipo": "Airbus A320", "da": "Roma", "a": "Milano", "callsign": "AZ1"}]
    app.planes_at = time.time()
    text, card = app._f_radar()
    assert "7 km" in text and text.startswith("Un aereo qui intorno: ")


def test_bubble_does_not_hang_on_long_texts_or_cards(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, show_minutes=20, card_seconds=40))
    long = app.char.wrap("Caro diario, " + "oggi è stata una giornata lunga e piena di cose. " * 6, app.font_path)
    assert len(long) > 1
    app.msg = {"pages": long, "t0": time.time() - (len(long) * coinquilino.PAGE_SECS * 2 + 31), "kind": "filler"}
    assert app._bubble()[0] == "" and app.msg is None
    app.msg = {"pages": ["Ciao."], "t0": time.time() - 21 * 60, "kind": "filler", "card": object()}
    assert app._bubble()[0] == ""
    app.msg = {"pages": ["Ciao."], "t0": time.time() - 600, "kind": "filler"}
    assert app._bubble()[0] == "Ciao."                              # frase corta: resta
