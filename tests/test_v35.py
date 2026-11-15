"""La 3.5: orologio, casa a icone, in riproduzione (CV), porte e finestre, attivita', notifiche urgenti
(CX), date "umane" per gli appuntamenti, l'album quasi vuoto (CZ)."""
from datetime import datetime, timedelta

from conftest import STATES
from test_app import DAY

import coinquilino
import grafici

PIENO = (grafici.FULL_W, grafici.FULL_H)
C = coinquilino.Coinquilino


def porta(nome, stato="on", dc="door"):
    return {"state": stato, "attributes": {"device_class": dc, "friendly_name": nome}}


def suona(**extra):
    at = {"media_title": "Bohemian Rhapsody", "media_artist": "Queen", "media_album_name": "A Night at the Opera",
          "media_position": 60, "media_duration": 354, "friendly_name": "Cucina"}
    at.update(extra)
    return {"state": "playing", "attributes": at}


# ------------------------------------------------------------------ disegni
def test_new_screens_draw(make_app, cube):
    f = make_app(dict(DAY, host=cube.host)).font_path
    assert grafici.schermata_orologio("14:05", "sabato 15 novembre", ("sole", 18), ("domani alle 18", "Dentista"),
                                      f).size == PIENO
    assert grafici.schermata_orologio("07:00", "lunedì 1 dicembre", None, None, f).size == PIENO
    for n in range(1, 7):
        voci = [("luce", 2, "luci accese", True), ("clima", 0, "clima", False), ("termometro", "21,5°", "in casa",
                False), ("goccia", "58%", "umidità", False), ("porta", 1, "aperta", True), ("x", 1, "y", False)]
        assert grafici.schermata_icone(voci[:n], f).size == PIENO
    assert grafici.schermata_musica(None, "Un titolo lunghissimo che va su due righe e oltre", "Artista", "Album",
                                    30, 200, False, f).size == PIENO
    assert grafici.schermata_musica(grafici.Image.new("RGB", (300, 300)), "T", None, None, None, None, True,
                                    f).size == PIENO
    assert grafici.schermata_porte([("Porta d'ingresso", True, "door"), ("Corridoio", False, "motion")] * 5,
                                   f).size == PIENO
    assert grafici.schermata_numeri("Attività di oggi", [("5.230", "passi Luca")], f).size == PIENO
    for liv in ("info", "avviso", "urgente", "ok", "boh"):
        assert grafici.schermata_avviso("Lavatrice", "La lavatrice ha finito: stendi i panni " * 6, liv,
                                        f).size == PIENO


# ------------------------------------------------------------------ date umane
def test_human_dates():
    now = datetime(2026, 11, 15, 10, 0)                   # domenica
    q = C._quando
    assert q(now + timedelta(minutes=20), False, now) == "fra 20 minuti"
    assert q(datetime(2026, 11, 15, 15, 30), False, now) == "oggi alle 15:30"
    assert q(datetime(2026, 11, 15, 20, 0), False, now) == "stasera alle 20"
    assert q(datetime(2026, 11, 16, 18, 0), False, now) == "domani alle 18"
    assert q(datetime(2026, 11, 21, 0, 0), True, now) == "sabato"
    assert q(datetime(2026, 11, 25, 9, 0), False, now) == "fra 10 giorni"
    assert q(datetime(2026, 11, 15), True, now) == "oggi"


def test_agenda_tells_the_next_appointment(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, calendars=["calendar.famiglia"]))
    domani = (datetime.now() + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
    app.cal_events = [{"summary": "Dentista", "start": domani.isoformat()},
                      {"summary": "Passato", "start": (datetime.now() - timedelta(hours=30)).isoformat()}]
    assert app._prossimo_appuntamento() == ("domani alle 18", "Dentista")
    assert app._f_agenda() == "Prossimo appuntamento domani alle 18: Dentista."
    text, img = app._f_schermo_orologio()
    assert "domani alle 18: Dentista" in text and img.size == PIENO


# ------------------------------------------------------------------ casa a icone, porte, attivita'
def test_icons_screen(make_app, cube):
    states = dict(STATES, **{"light.a": {"state": "on", "attributes": {}}, "light.b": {"state": "on", "attributes": {}},
                             "binary_sensor.porta": porta("Porta", "off")})
    app = make_app(dict(DAY, host=cube.host), states=states)
    text, img = app._f_schermo_icone()
    assert text.startswith("2 luci accese") and img.size == PIENO


def test_doors_screen_only_when_something_is_open(make_app, cube):
    states = dict(STATES, **{"binary_sensor.porta": porta("Porta di casa"),
                             "binary_sensor.finestra": porta("Finestra salone", "off", "window"),
                             "binary_sensor.mov": porta("Movimento corridoio", "on", "motion"),
                             "binary_sensor.acqua": porta("Perdita", "on", "moisture")})
    app = make_app(dict(DAY, host=cube.host), states=states)
    assert {n for n, _, _ in app._porte()} == {"Porta di casa", "Finestra salone", "Movimento corridoio"}
    text, img = app._f_schermo_porte()
    assert text == "Aperta: Porta di casa." and img.size == PIENO
    states["binary_sensor.porta"]["state"] = "off"
    assert app._f_schermo_porte() is None                 # il movimento da solo non basta


def test_activity_screen_only_with_the_option(make_app, cube):
    passi = {"state": "5230", "attributes": {"unit_of_measurement": "steps", "friendly_name": "iPhone di Mario Steps"}}
    states = dict(STATES, **{"sensor.iphone_steps": passi})
    assert make_app(dict(DAY, host=cube.host), states=states)._f_schermo_attivita() is None
    app = make_app(dict(DAY, host=cube.host, activity_entities="sensor.iphone_steps"), states=states, name="passi")
    text, img = app._f_schermo_attivita()
    assert text == "Attività di oggi: iPhone Mario 5.230 passi." and img.size == PIENO


# ------------------------------------------------------------------ in riproduzione (CV)
def test_music_screen_when_playing(make_app, cube):
    states = dict(STATES, **{"media_player.cucina": suona(), "media_player.tv": {"state": "off", "attributes": {}}})
    app = make_app(dict(DAY, host=cube.host), states=states)
    text, img = app._f_schermo_musica()
    assert text == "In riproduzione: Bohemian Rhapsody di Queen." and img.size == PIENO
    states["media_player.cucina"]["state"] = "paused"
    assert app._f_schermo_musica() is None


def test_music_cover_url(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host, ha_mcp_url="http://192.168.1.50:8123/api/mcp", ha_mcp_token="x"))
    assert app.ha_url == "http://192.168.1.50:8123"
    partiti = []
    monkeypatch.setattr(coinquilino.threading, "Thread", lambda target, daemon: type(
        "T", (), {"start": lambda self: partiti.append(target)})())
    assert app._copertina("/api/media_player_proxy/media_player.cucina?token=abc") is None
    assert "http://192.168.1.50:8123/api/media_player_proxy/media_player.cucina?token=abc" in app._covers
    assert len(partiti) == 1
    app._copertina("/api/media_player_proxy/media_player.cucina?token=abc")
    assert len(partiti) == 1                              # gia' chiesta: non si riscarica


def test_music_screen_refreshes_and_goes_away(make_app, cube):
    states = dict(STATES, **{"media_player.cucina": suona()})
    app = make_app(dict(DAY, host=cube.host, talk_every_minutes=0), states=states)
    app.filler_order = ["schermo_musica"]
    app._filler({})
    assert app.msg["refresh"] == "schermo_musica"
    app.msg["t0"] -= 120
    states["media_player.cucina"]["state"] = "idle"
    app._refresh_screen(app.msg)
    assert app.msg is None                                # la musica e' finita: via la schermata


# ------------------------------------------------------------------ notifiche urgenti (CX)
def test_urgent_notification_on_the_whole_cube(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._say_event("coinquilino_say", {"text": "La lavatrice ha finito.", "urgent": "ok", "title": "Lavatrice",
                                       "seconds": 300}, {})
    assert app.msg["text"] == "La lavatrice ha finito." and app.msg["screen"].size == PIENO
    assert app._bubble_life(app.msg) == 300
    app._say_event("coinquilino_say", {"text": "Allarme!", "urgent": True}, {})
    assert app.msg["screen"].size == PIENO and "life" not in app.msg


# ------------------------------------------------------------------ album quasi vuoto (CZ)
def test_asks_for_photos_when_the_album_is_almost_empty(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host))
    mandati = []
    monkeypatch.setattr(app, "_notify", lambda text, kind=None: mandati.append(text) or True)
    app.tg_chats = [123]
    monkeypatch.setattr(coinquilino, "datetime", type("D", (datetime,), {"now": staticmethod(
        lambda: datetime(2026, 11, 15, 11, 0))}))
    app._photo_ask()
    assert len(mandati) == 1 and "foto" in mandati[0]
    app._photo_ask()
    assert len(mandati) == 1                              # una volta ogni photo_ask_days
    app.mem["foto_chieste"] = 0
    app.photo_ask_below = 0
    app._photo_ask()
    assert len(mandati) == 1                              # 0: mai


def test_new_kinds_have_topics():
    for k in ("schermo_orologio", "schermo_icone", "schermo_musica", "schermo_porte", "schermo_attivita"):
        assert k in coinquilino.TOPIC and k in coinquilino.CHATTER_EVERY and k in coinquilino.CHATTER_DAY


# ------------------------------------------------------------------ 3.5.1: sistema e anteprima
def pct(v, nome, unita="%"):
    return {"state": str(v), "attributes": {"unit_of_measurement": unita, "friendly_name": nome}}


def test_system_screen_from_system_monitor(make_app, cube):
    states = dict(STATES, **{
        "sensor.system_monitor_utilizzo_del_processore": pct(12.4, "Utilizzo del processore"),
        "sensor.system_monitor_utilizzo_della_memoria": pct(1237, "Utilizzo della memoria", "MiB"),
        "sensor.system_monitor_utilizzo_della_memoria_2": pct(63.3, "Utilizzo della memoria"),
        "sensor.system_monitor_disk_usage": pct(22, "Disk usage /"),
        "sensor.system_monitor_utilizzo_swap": pct(90, "Utilizzo Swap"),
        "sensor.system_monitor_carico_5_min": pct(0.35, "Carico (5 min)", None)})
    app = make_app(dict(DAY, host=cube.host), states=states)
    voci, carico = app._sistema()
    assert voci == [("CPU", 12.4), ("Memoria", 63.3), ("Disco", 22.0)] and carico == 0.35
    text, img = app._f_schermo_sistema()
    assert text == "Home Assistant: cpu al 12%, memoria al 63%, disco al 22%." and img.size == PIENO
    assert grafici.colore_uso(30) == grafici.GREEN and grafici.colore_uso(90) == grafici.RED


def test_system_screen_needs_the_sensors(make_app, cube):
    assert make_app(dict(DAY, host=cube.host))._f_schermo_sistema() is None


def test_preview_saves_a_frame_held_back_by_the_30_seconds(make_app, cube, tmp_path):
    app = make_app(dict(DAY, host=cube.host, preview=str(tmp_path / "p.png")))
    a, b = grafici.Image.new("RGB", (240, 200), "red"), grafici.Image.new("RGB", (240, 200), "blue")
    app._save_preview(a)
    app._save_preview(b)                                  # dentro i 30 secondi: tenuto da parte
    assert app._preview_wait is b
    app.preview_at -= 31
    app._save_preview(app._preview_wait)
    assert app._preview_wait is None
    assert grafici.Image.open(tmp_path / "p.png").getpixel((5, 5)) == (0, 0, 255)


# ------------------------------------------------------------------ 3.5.2: casa a icone sensata
def test_icons_only_what_makes_sense_here(make_app, cube):
    ir = {"state": "cool", "attributes": {"friendly_name": "Condizionatore", "current_temperature": 24}}
    states = dict(STATES, **{"climate.ir_1": ir, "climate.ir_2": dict(ir, state="auto"),
                             "light.a": {"state": "on", "attributes": {}},
                             "binary_sensor.finestra": porta("Finestra", "off", "window")})
    app = make_app(dict(DAY, host=cube.host), states=states)
    _, img = app._f_schermo_icone()
    tipi = [v[0] for v in app._icone_voci()]
    assert "clima" not in tipi                            # i telecomandi IR non sanno se e' acceso
    assert "porta" not in tipi                            # tutto chiuso: "0 aperte" non serve
    tado = {"state": "heat", "attributes": {"hvac_action": "heating", "current_temperature": 20}}
    states2 = dict(states, **{"climate.tado": tado, "binary_sensor.finestra": porta("Finestra", "on", "window")})
    voci = {v[0]: v for v in make_app(dict(DAY, host=cube.host), states=states2, name="due")._icone_voci()}
    assert voci["clima"][1] == 1 and voci["porta"][1] == 1
