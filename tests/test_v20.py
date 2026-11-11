"""La 2.0: piu' utile e meno infantile, meteo a confronto, scene del giorno, schermate, casa che
cambia, citofono, batterie, aspetto da ragazzino."""
import time
from datetime import date, timedelta

import alessio
import coinquilino
import grafici
import meteo
from conftest import STATES
from test_app import DAY
from test_v14 import services


def week(tmax, tmin=None, rain=None, mm=None, codes=None, today_at=7):
    """Previsioni finte con le date: oggi e' il giorno today_at della lista."""
    n = len(tmax)
    t0 = date.today() - timedelta(days=today_at)
    days = [(t0 + timedelta(days=k)).isoformat() for k in range(n)]
    return {"daily": {
        "time": days, "temperature_2m_max": tmax,
        "temperature_2m_min": tmin or [t - 8 for t in tmax],
        "precipitation_probability_max": rain or [0] * n, "precipitation_sum": mm or [0] * n,
        "weather_code": codes or [0] * n, "wind_gusts_10m_max": [10] * n,
        "sunrise": [f"{d}T06:40" for d in days], "sunset": [f"{d}T{17 - k // 6:02d}:{50 - k:02d}" for k, d in
                                                            enumerate(days)]}}


# ------------------------------------------------------------------ meteo dei giorni
def test_today_index_and_comparisons():
    gg = meteo.giorni(week([20, 21, 20, 19, 21, 20, 19, 19, 14, 13, 14]))
    i = meteo.oggi_i(gg)
    assert i == 7 and gg[i]["data"] == date.today()
    assert meteo.confronti(gg, i)[0] == "Domani 5 gradi in meno di oggi: massima 14."
    assert meteo.rispetto_a_ieri(gg, i) == ""                       # uguale a ieri: niente da dire
    gg2 = meteo.giorni(week([20, 20, 20, 20, 20, 20, 23, 19, 19, 19, 19]))
    assert meteo.rispetto_a_ieri(gg2, 7) == "Oggi 4 gradi più freddo di ieri."


def test_rain_coming_and_rain_ending():
    dry_then_rain = week([18] * 11, rain=[0] * 8 + [90, 80, 0], mm=[0] * 8 + [6, 4, 0],
                         codes=[0] * 8 + [63, 61, 0])
    gg = meteo.giorni(dry_then_rain)
    assert meteo.confronti(gg, 7)[0] == "Dopo giorni asciutti, pioggia in arrivo domani."
    wet = week([18] * 11, rain=[0] * 5 + [90, 90, 90, 0, 0, 0], mm=[0] * 5 + [5, 6, 3, 0, 0, 0],
               codes=[0] * 5 + [63, 63, 61, 1, 0, 0])
    assert meteo.confronti(meteo.giorni(wet), 7)[0] == "Da domani torna il sereno, dopo 3 giorni di pioggia."


def test_daylight_compared_with_last_week():
    gg = meteo.giorni(week([18] * 11))
    minuti, diff = meteo.luce(gg, 7)
    assert minuti > 600 and diff < 0                                # in autunno le giornate si accorciano


def test_old_forecast_without_dates_still_works():
    gg = meteo.giorni({"daily": {"temperature_2m_min": [11, 11], "temperature_2m_max": [20, 20],
                                 "precipitation_probability_max": [10, 70]}})
    assert meteo.oggi_i(gg) == 0 and meteo.cielo(gg[1]) == "pioggia"


def test_weekly_chart_instead_of_obvious_hours(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.forecast = week([20, 21, 20, 19, 21, 20, 19, 19, 14, 13, 14])
    text, card = app._f_grafico_meteo()
    assert text == "Domani 5 gradi in meno di oggi: massima 14." and card.size == (grafici.CARD_W, grafici.CARD_H)
    full = app._f_schermo_meteo()[1]
    assert full.size == (240, 200)


def test_morning_says_the_difference_with_yesterday(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, owner="Zio Mario"))
    app.forecast = week([20, 20, 20, 20, 20, 20, 23, 19, 19, 19, 19])
    gg, i = app._giorni()
    fact = {"kind": "morning", "tmin": 11, "tmax": 19, "rain": 0, "gust": 10,
            "confronto": meteo.rispetto_a_ieri(gg, i)}
    text, _ = app._write(fact)
    assert text == "Buongiorno Zio Mario: oggi tra 11 e 19 gradi. Oggi 4 gradi più freddo di ieri."


def test_weather_change_told_once_a_day(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host))
    app.forecast = week([20, 21, 20, 19, 21, 20, 19, 19, 14, 13, 14])

    class Afternoon(coinquilino.datetime):
        @classmethod
        def now(cls, tz=None):
            return coinquilino.datetime.combine(date.today(), coinquilino.datetime.min.time()).replace(hour=15)
    monkeypatch.setattr(coinquilino, "datetime", Afternoon)
    app._weather_change()
    app._weather_change()
    assert [f["text"] for f in app.queue if f["kind"] == "forecast_change"] == [
        "Domani 5 gradi in meno di oggi: massima 14."]


# ------------------------------------------------------------------ tono ed eta'
def test_fixed_age_ten_and_useful_persona(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    assert app.anni == 10 and alessio.AGE == 10
    assert "Hai 10 anni" in app.persona and "ragazzino" in app.persona
    assert "Prima di tutto sei utile" in app.persona
    assert "biberon" not in app.persona and "piccolissimo" not in app.persona
    app.mem["nascita"] = "2000-01-01"
    app._daily({})
    assert not [f for f in app.queue if f["kind"] == "crescita"]     # non cresce piu' da solo
    assert make_app(dict(DAY, host=cube.host, age=12)).anni == 12


def test_no_baby_words_in_fixed_lines(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    for tpl in list(coinquilino.FALLBACK_ALESSIO.values()) + list(coinquilino.KIND_HINT.values()):
        assert not any(w in tpl.lower() for w in ("biberon", "pappa", "ciao ciao", "pozzanghere", "da bimbo"))
    assert "biberon" not in (app._f_api() or ("",))[0]


# ------------------------------------------------------------------ ripetizioni
def test_news_told_once_a_day(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.recent_news.extend([("Dalla città", "La Corte dei Conti promuove il piano"), ("Il Post", "Altro")])
    app._chatter_told(coinquilino.clean(app.T("Dalla città: La Corte dei Conti promuove il piano")))
    app.chatter_said.clear()                                       # anche passate le 3 ore...
    assert [t for _, t in app._news_fresh()] == ["Altro"]           # ...oggi non torna


def test_daily_cap_per_chatter_kind(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, chatter_day_max={"calendar.today": 0}))
    assert app.chatter_day["giorno"] == 0
    for _ in range(3):
        app._chatter_count("chi", add=True)
    assert app._chatter_count("chi") == 3 >= app.chatter_day["chi"]


def test_photos_every_thirty_minutes_by_default(make_app, cube):
    assert make_app(dict(DAY, host=cube.host)).photo_every == 30


# ------------------------------------------------------------------ scene e schermate
def test_scene_uses_interests_not_blocked(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    for k in list(app.carattere.interessi):
        app.carattere.interessi[k] = 0
    app.carattere.interessi["spazio"] = 9
    sc = app._scene()
    assert sc["oggetto"] in ("razzo", "libri", "pianta") and sc["giorno"] == date.today().day
    assert sc["stagione"] == alessio.stagione(date.today())
    app.carattere.blocca("spazio")
    app._scene_day = None
    assert app._scene()["oggetto"] != "razzo"
    img = alessio.render(font_path=app.font_path, scene=sc, weather="fog")
    assert img.size == (240, 200)


def test_seasons():
    assert [alessio.stagione(date(2026, m, 1)) for m in (1, 4, 7, 10)] == [
        "inverno", "primavera", "estate", "autunno"]


def test_home_screen_and_power_screen(make_app, cube):
    states = dict(STATES, **{"sensor.studio": {"state": "21.4", "attributes": {"friendly_name": "Temperatura studio"}},
                             "sensor.potenza": {"state": "412", "attributes": {}},
                             "sensor.energia": {"state": "6.3", "attributes": {}}})
    app = make_app(dict(DAY, host=cube.host, indoor_temperature=["sensor.studio"],
                        nicknames={"person.mario": "Mario"}), states=states)
    text, img = app._f_schermo_casa()
    assert text == "In casa: Mario." and img.size == (240, 200)
    assert app._room_name("sensor.studio") == "Studio"
    assert app._f_schermo_consumi() is None                          # senza sensori: niente schermata
    app.power_sensor, app.energy_sensor = "sensor.potenza", "sensor.energia"
    app.mem["energia"] = {(date.today() - timedelta(days=1)).isoformat(): 8.1}
    text, img = app._f_schermo_consumi()
    assert text == "Corrente: oggi 6,3 kWh finora, ieri 8,1 in tutto." and img.size == (240, 200)


def test_screen_shown_full_cube(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, talk_every_minutes=0, nicknames={"person.mario": "Mario"}))
    app.filler_order = ["schermo_casa"]
    app._filler({})
    assert app.msg["screen"].size == (240, 200) and "card" not in app.msg


# ------------------------------------------------------------------ la casa che cambia
def test_room_warming_and_window_guess(make_app, cube):
    states = dict(STATES, **{"sensor.studio": {"state": "20", "attributes": {"friendly_name": "Studio"}}})
    app = make_app(dict(DAY, host=cube.host, indoor_temperature=["sensor.studio"]), states=states)
    t = time.time()
    for k, v in enumerate((20, 20.4, 20.8, 21.2, 21.6, 22.0, 22.1)):
        states["sensor.studio"]["state"] = str(v)
        app._rooms_sample(t + k * 600)
    assert [f["text"] for f in app.queue if f["kind"] == "room_change"] == [
        "Studio: la temperatura è salita di 2,1 gradi in un'ora, ora 22,1 gradi."]
    app2 = make_app(dict(DAY, host=cube.host, indoor_temperature=["sensor.studio"]), states=states, name="altro")
    for k, v in enumerate((21, 21, 20, 18.6)):
        states["sensor.studio"]["state"] = str(v)
        app2._rooms_sample(t + k * 600)
    assert app2.queue[-1]["text"] == "Studio: 2,4 gradi in meno in mezz'ora, ora 18,6 gradi. Finestra aperta?"


# ------------------------------------------------------------------ citofono
DOOR = dict(DAY, doorbell="event.citofono_ding", doorbell_open="event.citofono_apri", notify="notify.tel")


def test_greeting_right_after_door_opened(make_app, cube):
    app = make_app(dict(DOOR, host=cube.host))
    calls = []
    app.run_in = lambda cb, sec, **kw: calls.append(sec)
    app.open_at = time.time() - 30
    app._person("person.anna", "state", "not_home", "home", {})
    assert calls == [1] and any("dopo l'apertura" in m for _, m in app.logs)


def test_say_event_can_go_to_telegram(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, notify="notify.tel"))
    app.mem["ultimo_messaggio"] = time.time()
    app._say_event("coinquilino_say", {"text": "Lavatrice finita", "telegram": True}, {})
    assert services(app, "notify/tel")[0]["message"] == "Lavatrice finita"


# ------------------------------------------------------------------ batterie

# ------------------------------------------------------------------ aspetto
def test_looks_older_at_ten():
    alessio.AGE = 2
    small = alessio.render()
    alessio.AGE = 10
    big = alessio.render()
    def near(a, b):
        return max(abs(x - y) for x, y in zip(a, b, strict=True)) <= 3
    assert near(big.getpixel((180, 195)), alessio.SHIRT) and not near(small.getpixel((180, 195)), alessio.SHIRT)
    assert near(big.getpixel((150, 70)), alessio.HAIR) and not near(small.getpixel((150, 70)), alessio.HAIR)
