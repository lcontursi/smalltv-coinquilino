"""La 1.6: foto a giro, foto da Telegram, aerei meno spesso, messaggi spontanei con tetto."""
import os
import time

from PIL import Image

import alessio
import coinquilino
import foto
from test_app import DAY, Resp
from test_v15 import TG, HOUSE, Now, obey, sent


def img(w, h, color=(200, 80, 40)):
    return Image.new("RGB", (w, h), color)


# ------------------------------------------------------------------ foto
def test_photo_frames():
    assert foto.quadro(img(4000, 3000)).size == (220, 180)
    portrait = foto.quadro(img(3000, 4000, (255, 255, 255)))
    assert portrait.size == (220, 180)
    assert portrait.getpixel((5, 90)) != (255, 255, 255)          # ai lati lo sfondo sfocato e scurito
    assert portrait.getpixel((110, 90)) == (255, 255, 255)        # al centro la foto intera
    shot = alessio.render_photo(foto.quadro(img(4000, 3000)))
    assert shot.size == (240, 200)


def test_album_rotation_and_limit(tmp_path):
    al = foto.Album(str(tmp_path / "album"), massimo=3)
    names = []
    for i in range(4):
        names.append(al.aggiungi(img(400, 300, (i * 50, 0, 0))))
        time.sleep(0.01)
    assert al.foto() == sorted(names)[1:]                          # la piu' vecchia e' uscita
    giro = [al.prossima()[0] for _ in range(4)]
    assert giro[:3] == al.foto() and giro[3] == al.foto()[0]       # a giro, in ordine


def photo_app(make_app, cube, tmp_path, **kw):
    inbox = tmp_path / "telegram_bot"
    inbox.mkdir(exist_ok=True)
    app = make_app(dict(DAY, host=cube.host, photo_inbox=str(inbox), **kw))
    return app, inbox


def test_inbox_import_shows_new_photo_and_ignores_other_files(make_app, cube, tmp_path):
    app, inbox = photo_app(make_app, cube, tmp_path)
    img(800, 600).save(inbox / "coinquilino_1.jpg")
    img(800, 600).save(inbox / "altro_file.jpg")                  # non e' nostra: non si tocca
    old = time.time() - 60
    for f in inbox.iterdir():
        os.utime(f, (old, old))
    app._photo_turn({})
    assert app.photo and app.photo["until"] > time.time() + 30
    assert sorted(os.listdir(inbox)) == ["altro_file.jpg"] and len(app.album.foto()) == 1
    assert {"name": "Pixel", "hold_s": 42} in cube.channels


def test_photo_rotation_every_ten_minutes(make_app, cube, tmp_path):
    app, _ = photo_app(make_app, cube, tmp_path, photo_every_minutes=10)    # dalla 2.0 il predefinito e' 30
    app.album.aggiungi(img(400, 300))
    app.last_photo = time.time() - 300
    app._photo_turn({})
    assert app.photo is None                                      # non sono passati 10 minuti
    app.last_photo = time.time() - 601
    app._photo_turn({})
    assert app.photo


def test_no_photos_at_night(make_app, cube, tmp_path):
    app, _ = photo_app(make_app, cube, tmp_path, night_start=0, night_end=24)
    app.album.aggiungi(img(400, 300))
    app.last_photo = 0
    app._photo_turn({})
    assert app.photo is None


def test_telegram_photo_is_downloaded_with_our_name(make_app, cube, tmp_path, monkeypatch):
    """L'evento vero del 30/10 (dati finti)."""
    monkeypatch.setattr(coinquilino.threading, "Thread", Now)
    app = obey(make_app(dict(TG, host=cube.host, photo_inbox=str(tmp_path)), states=HOUSE))
    app._tg_bus("telegram_attachment", {
        "id": 37, "chat_id": 111, "date": "2026-10-30T10:16:50+00:00", "text": None,
        "file_id": "AgACAgQAAxkB", "file_mime_type": "image/jpeg", "file_size": 85361, "user_id": 111,
        "bot": {"config_entry_id": "01ABC", "username": "ha_alessio_bot"}}, {})
    dl = [kw for s, kw in app.services if s == "telegram_bot/download_file"]
    assert dl and dl[0]["file_id"] == "AgACAgQAAxkB" and dl[0]["file_name"].startswith("coinquilino_")
    assert sent(app)[-1]["message"].startswith("📷")


def test_telegram_photo_from_unknown_chat_ignored(make_app, cube, tmp_path, monkeypatch):
    app = make_app(dict(TG, host=cube.host, photo_inbox=str(tmp_path)), states=HOUSE)
    app._tg_bus("telegram_attachment", {"chat_id": 999, "file_id": "x", "file_mime_type": "image/jpeg"}, {})
    assert not [s for s, _ in app.services if s == "telegram_bot/download_file"]


# ------------------------------------------------------------------ aerei ("troppo fissato")
def test_planes_at_most_once_an_hour(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._say_now("Un aereo! È un Airbus A320 a 10.000 metri.", "plane")
    assert not app._plane_ok()
    app.planes = [{"km": 5, "flight": "X", "lat": 0, "lon": 0, "alt_m": 10000, "hex": "abc"}]
    app.planes_at = time.time()
    ctx = " ".join(app._context(full=True))
    assert "Il più vicino adesso" not in ctx and "Aerei visti oggi" not in ctx
    app.last_plane_talk -= 3601
    assert app._plane_ok() and "Il più vicino adesso" in " ".join(app._context(full=True))


def test_director_talking_about_planes_counts(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._say_now("Zio Mario, oggi ho visto 6 aerei dalla finestra!", "regista")
    assert not app._plane_ok()


# ------------------------------------------------------------------ tetto dei messaggi
def test_one_message_every_three_hours_except_reminders(make_app, cube, monkeypatch):
    monkeypatch.setattr(coinquilino.threading, "Thread", Now)
    app = obey(make_app(dict(TG, host=cube.host), states=HOUSE))
    assert app._notify("Primo avviso", kind="regista")
    assert not app._notify("Secondo avviso", kind="action")
    assert app._notify("Zio Mario, ti ricordo: la pasta!", kind="reminder")
    assert [m["message"] for m in sent(app)] == ["Primo avviso", "Zio Mario, ti ricordo: la pasta!"]
    assert any(m.startswith("SKIP") and "ultimo messaggio" in m for _, m in app.logs)


def test_spontaneous_idea_sent_once_and_vote_recorded(make_app, cube, monkeypatch):
    class Day(coinquilino.datetime):
        @classmethod
        def now(cls, tz=None):
            return coinquilino.datetime.combine(coinquilino.date.today(),
                                                coinquilino.datetime.min.time()).replace(hour=11)
    monkeypatch.setattr(coinquilino, "datetime", Day)
    app = obey(make_app(dict(TG, host=cube.host), states=HOUSE))
    app._apply_night("idee", "<tipo>funzione</tipo><idea>Vuoi che ti dica la mattina le temperature?</idea>")
    app._spontaneous_turn({})
    app._spontaneous_turn({})
    msgs = [m for m in sent(app) if "temperature" in m["message"]]
    assert len(msgs) == 1 and msgs[0]["message"].startswith("💡")
    n = msgs[0]["inline_keyboard"][0].split("/su ")[1].split(",")[0]
    app._tg_button("111", "Zio Mario", {"data": f"/su {n}", "id": "c"})
    assert app.mem["proposte"][0]["voto"] == "su"
    with open(os.path.join(app.app_dir, "proposte.md"), encoding="utf-8") as f:
        assert "👍" in f.read()


def test_weekly_summary_saved_from_character_job(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._apply_night("carattere", '<carattere>{"tratti": {}, "interessi": {}}</carattere>'
                     "<riassunto>Che settimana, zio!</riassunto><curiosita>[]</curiosita>")
    assert app.mem["riassunto"]["testo"] == "Che settimana, zio!"


def test_state_sensor_for_dashboard(make_app, cube, tmp_path):
    app = make_app(dict(DAY, host=cube.host, preview=str(tmp_path / "cubo.png")))
    app.ricordi.add("Zio Mario rientra verso le 19")
    app._L("ACT", "free", "chat", "home.action", "light/turn_off light.studio: chiesto da Zio Mario")
    app._publish_state()
    state, attrs = app.published["sensor.alessio_stato"]
    assert state in coinquilino.MOODS or state == "happy"
    assert attrs["ricordi"] == ["Zio Mario rientra verso le 19."]
    assert "light/turn_off light.studio" in attrs["azioni"][0] and attrs["versione"] == coinquilino.VERSION
    app._save_preview(Image.new("RGB", (240, 200)))
    assert (tmp_path / "cubo.png").exists()


def test_photo_goes_to_the_cube(make_app, cube, tmp_path):
    app, _ = photo_app(make_app, cube, tmp_path)
    app._photo_show(foto.quadro(img(800, 600, (10, 200, 30))), "x.png")
    app.next_at = 0
    app._tick({})
    assert cube.frames and cube.frames[-1][0] == {"x": 0, "y": 0, "w": 240, "h": 200}
    n = len(cube.frames)
    app.next_at = 0
    app._tick({})
    assert len(cube.frames) == n                                  # foto ferma: niente altro traffico


# ------------------------------------------------------------------ 1.7
def test_lotto_and_funerals_filtered():
    feed = {"skip": []}
    item = lambda t: {"title": t, "desc": "", "cats": []}          # noqa: E731
    assert coinquilino.Coinquilino._skip_news(
        item("Lotto, la Puglia regina delle vincite. Oltre 50mila euro vinti tra Specchia e Taranto"), feed)
    assert coinquilino.Coinquilino._sad("Commemorazione dei defunti, a Bologna cimitero aperto e navette gratuite")
    assert not coinquilino.Coinquilino._skip_news(item("Il Bologna vince in trasferta"), feed)


def test_director_marks_the_news_it_used(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.recent_news.extend([("Il Post", "La BCE ha lasciato invariati i tassi"), ("Il Post", "Nuovo museo a Roma")])
    ctx = " ".join(app._context(full=True))
    assert "[1] La BCE ha lasciato invariati i tassi" in ctx
    app._news_picked("<umore>happy</umore><notizia>1</notizia><frase>…</frase>")
    ctx = " ".join(app._context(full=True))
    assert "BCE" not in ctx and "[1] Nuovo museo a Roma" in ctx
    assert [t for _, t in app._news_fresh()] == ["Nuovo museo a Roma"]


def test_appearance_only_when_asked(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, feste=False))       # senza festa (oggi potrebbe esserci)
    assert "Come sei adesso" not in " ".join(app._context())
    assert "Come sei adesso" in " ".join(app._context(chat_text="com'è il tuo aspetto oggi?"))


def test_tics_stay_banned_for_a_week(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, owner="Zio Mario"))
    for t in ["Ciao! Ti voglio tanto bene!", "Piove. Ti voglio tanto bene!"]:
        app._say_now(t, "chat", cost="paid")
    assert "ti voglio tanto bene" in app._tics()
    for i in range(10):                                           # sparisce dalle ultime frasi...
        app._say_now(f"Frase diversa numero {i}.", "chat", cost="paid")
    assert "ti voglio tanto bene" in app._tics()                  # ...ma resta vietato
    old = (coinquilino.date.today() - coinquilino.timedelta(days=8)).isoformat()
    app.mem["tormentoni"]["ti voglio tanto bene"] = old
    assert "ti voglio tanto bene" not in app._tics()


def test_night_idea_gets_the_tic_rule(make_app, cube):
    app = make_app(dict(TG, host=cube.host, owner="Zio Mario"), states=HOUSE)
    app.mem["tormentoni"] = {"booo": coinquilino.date.today().isoformat()}
    app.remember("è tornato a casa: Zio Mario")
    req = next(r for r in app._night_requests() if r["kind"] == "idee")
    assert "«booo»" in req["params"]["messages"][0]["content"]


def test_terminate_saves_chatter_memory(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._chatter_told("Dalla città: Una notizia")
    app.terminate()
    app2 = make_app(dict(DAY, host=cube.host))
    assert "Dalla città: Una notizia" in app2.chatter_said


def test_unreachable_cube_does_not_flood_the_log(make_app):
    app = make_app(dict(DAY, host="127.0.0.1:9"))                  # nessuno risponde
    for _ in range(5):
        app._show_channel()
    assert len([m for _, m in app.logs if "non riesco a cambiare canale" in m]) == 1
    app.fail = 5
    app._show_channel()                                           # cubo giu' da un po': non ci prova
    assert len([m for _, m in app.logs if "non riesco a cambiare canale" in m]) == 1


# ------------------------------------------------------------------ album gestibile (1.7)
def test_album_takes_pictures_dropped_in_its_folder(tmp_path):
    al = foto.Album(str(tmp_path / "media"))
    img(1200, 900).save(tmp_path / "media" / "vacanze.jpg")
    old = time.time() - 60
    os.utime(tmp_path / "media" / "vacanze.jpg", (old, old))
    (tmp_path / "media" / "rotto.jpg").write_bytes(b"non e' una foto")
    os.utime(tmp_path / "media" / "rotto.jpg", (old, old))
    nuove, errori = al.sincronizza()
    assert len(nuove) == 1 and len(errori) == 1 and "rotto.jpg" in errori[0]
    assert sorted(os.listdir(tmp_path / "media")) == sorted(nuove)
    assert foto.Album.etichetta("20261030-113200-302.png") == "30/10 11:32"


def test_old_album_moves_to_new_folder(make_app, cube, tmp_path):
    old = tmp_path / "apps" / "foto"
    old.mkdir(parents=True)
    img(220, 180).save(old / "20261030-113200-302.png")
    app = make_app(dict(DAY, host=cube.host, photo_dir=str(tmp_path / "media_c")))
    assert app.album.foto() == ["20261030-113200-302.png"] and not old.exists()


def test_dashboard_select_show_and_delete(make_app, cube, tmp_path):
    states = dict(HOUSE, **{"input_select.alessio_foto": {"state": "", "attributes": {}},
                            "input_button.mostra": {"state": "x", "attributes": {}},
                            "input_button.togli": {"state": "x", "attributes": {}}})
    app = make_app(dict(DAY, host=cube.host, photo_select="input_select.alessio_foto",
                        photo_show_button="input_button.mostra", photo_delete_button="input_button.togli"),
                   states=states)
    a = app.album.aggiungi(img(400, 300))
    app._photo_options()
    opts = [kw for s, kw in app.services if s == "input_select/set_options"][-1]["options"]
    assert opts == [foto.Album.etichetta(a)]
    app.states["input_select.alessio_foto"] = {"state": opts[0], "attributes": {}}
    app._photo_btn_show("input_button.mostra", "state", "1", "2", {})
    assert app.photo and app.photo["nome"] == a
    app._photo_btn_delete("input_button.togli", "state", "1", "2", {})
    assert app.album.foto() == [] and app.photo is None
    assert [kw for s, kw in app.services if s == "input_select/set_options"][-1]["options"] == ["(nessuna foto)"]


def test_telegram_reply_togli_removes_that_photo(make_app, cube, tmp_path, monkeypatch):
    monkeypatch.setattr(coinquilino.threading, "Thread", Now)
    inbox = tmp_path / "tg"
    inbox.mkdir()
    app = obey(make_app(dict(TG, host=cube.host, photo_inbox=str(inbox)), states=HOUSE))
    app._tg_bus("telegram_attachment", {"id": 37, "chat_id": 111, "file_id": "F", "file_mime_type": "image/jpeg"}, {})
    nome = [kw for s, kw in app.services if s == "telegram_bot/download_file"][0]["file_name"]
    img(800, 600).save(inbox / nome)
    old = time.time() - 60
    os.utime(inbox / nome, (old, old))
    app._photo_turn({})
    assert len(app.album.foto()) == 1
    app._tg_bus("telegram_command", {"chat_id": 111, "command": "/foto", "text": "/foto", "id": 40}, {})
    assert sent(app)[-1]["message"].startswith("Nell'album ci sono 1 foto")
    app._tg_bus("telegram_text", {"chat_id": 222, "text": "togli", "id": 41, "reply_to_message_id": 37}, {})
    assert len(app.album.foto()) == 1                             # Anna non puo'
    app._tg_bus("telegram_text", {"chat_id": 111, "text": "togli", "id": 42, "reply_to_message_id": 37}, {})
    assert app.album.foto() == [] and sent(app)[-1]["message"] == "Fatto, l'ho tolta dall'album."


def test_photos_use_their_own_saturation(make_app, cube, tmp_path, monkeypatch):
    app, _ = photo_app(make_app, cube, tmp_path, photo_saturation=1.0)
    seen = []
    real = app._send
    monkeypatch.setattr(app, "_send", lambda img, box, sat=None, dim=True: (seen.append(sat), real(img, box, sat))[1])
    app._photo_show(foto.quadro(img(800, 600)), "x.png")
    app.next_at = 0
    app._tick({})
    assert seen == [1.0]


# ------------------------------------------------------------------ 1.8: il quadrante di Alessio
def test_night_face_of_alessio(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, night_start=0, night_end=24))
    assert app.night_clock == "alessio"
    app.next_at = 0
    app._tick({})
    assert cube.frames and cube.frames[-1][0] == {"x": 0, "y": 0, "w": 240, "h": 200}
    n = len(cube.frames)
    app.next_at = 0
    app._tick({})                                                 # stesso minuto: niente da mandare
    assert len(cube.frames) == n
    assert not [c for c in cube.channels if c.get("name") == "Night"]   # niente quadrante di glimmer
    cube.state["active"] = False                                  # il cubo e' su un altro canale
    app.next_at = 0
    app._tick({})
    assert cube.channels[-1] == {"name": "Pixel", "hold_s": 0}


def test_night_face_drawing():
    from datetime import datetime
    img = alessio.render_night(datetime(2026, 11, 1, 0, 45), os.path.join(
        os.path.dirname(coinquilino.__file__), "fonts", "Fredoka.ttf"))
    assert img.size == (240, 200)
    assert img.convert("L").getextrema()[1] < 200                 # niente di troppo luminoso


# ------------------------------------------------------------------ 1.8: pioggia, autonomia, idee
def fake_meteo(monkeypatch, precip):
    real = coinquilino.requests.get
    from datetime import datetime, timedelta

    def get(url, **kw):
        if "open-meteo" not in url:
            return real(url, **kw)
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        hours = [(now + timedelta(hours=i)).isoformat(timespec="minutes") for i in range(48)]
        j = {"current": {"temperature_2m": 15, "precipitation": precip["now"], "weather_code": 61},
             "hourly": {"time": hours, "temperature_2m": [15] * 48, "precipitation_probability": [10] * 48,
                        "precipitation": [0] * 48, "wind_gusts_10m": [5] * 48},
             "daily": {"temperature_2m_max": [18, 18], "temperature_2m_min": [12, 12],
                       "precipitation_probability_max": [50, 50], "wind_gusts_10m_max": [10, 10]}}
        return Resp(j)
    monkeypatch.setattr(coinquilino.requests, "get", get)


def test_rain_stop_needs_two_dry_checks_and_ha_agreement(make_app, cube, monkeypatch):
    p = {"now": 1.0}
    fake_meteo(monkeypatch, p)
    states = dict(HOUSE, **{"weather.casa": {"state": "rainy", "attributes": {"temperature": 17}}})
    app = make_app(dict(DAY, host=cube.host), states=states)
    app._weather({})                                              # piove
    p["now"] = 0.0
    app._weather({})                                              # un solo controllo asciutto
    assert not [f for f in app.queue if f["kind"] == "rain_stop"]
    app._weather({})                                              # due, ma HA dice ancora pioggia
    assert not [f for f in app.queue if f["kind"] == "rain_stop"]
    app.states["weather.casa"] = {"state": "cloudy", "attributes": {"temperature": 17}}
    app._weather({})
    assert [f for f in app.queue if f["kind"] == "rain_stop"]
    app.states["weather.casa"] = {"state": "pouring", "attributes": {"temperature": 17}}
    app._speak({})                                                # ricomincia: l'avviso si butta
    assert not [f for f in app.queue if f["kind"] == "rain_stop"]
    assert any("piove ancora" in m for _, m in app.logs)


def test_dashboard_actions_exclude_messages(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._L("ACT", "free", "event", "notify", "telegram: 💡 un'idea")
    app._L("ACT", "free", "chat", "home.action", "light/turn_off light.x: chiesto da Zio")
    assert len(app.acts) == 1 and "light/turn_off" in app.acts[0]


def test_ideas_know_votes_and_topics_to_avoid(make_app, cube):
    app = make_app(dict(TG, host=cube.host, owner="Zio Mario", ideas_avoid=["riscaldamento", "Tado"]),
                   states=HOUSE)
    app.mem["proposte"] = [{"data": "2026-10-31", "testo": "Controllo la temperatura del salotto",
                            "tipo": "funzione", "inviata": "2026-10-31", "voto": "giu"}]
    app.remember("è tornato a casa: Zio Mario")
    reqs = {r["kind"]: r["params"]["messages"][0]["content"] for r in app._night_requests()}
    assert "BOCCIATA" in reqs["idee"] and "riscaldamento, Tado" in reqs["idee"]
    assert "Niente ricordi sul tuo modo di parlare" in reqs["ricordi"]


# ------------------------------------------------------------------ 1.8.1 (dal log dell'01/11)
def test_banned_catchphrases_are_cut_from_the_line(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.mem["tormentoni"] = {"ti voglio tanto bene": "2026-11-01", "booo": "2026-11-01"}
    assert app._strip_tics("Zio Mario! Ho visto un aereo passare sopra casa, andava verso il mare! "
                           "Ti voglio tanto bene!") == \
        "Zio Mario! Ho visto un aereo passare sopra casa, andava verso il mare!"
    assert app._strip_tics("Zio Mario! Spengo le luci del balcone, booo! Ti voglio tanto bene!") == \
        "Zio Mario! Spengo le luci del balcone!"
    assert app._strip_tics("Ti voglio tanto bene!") == "Ti voglio tanto bene!"   # resterebbe vuota


def test_weekly_summary_and_ideas_rules(make_app, cube):
    app = make_app(dict(TG, host=cube.host, owner="Zio Mario"), states=HOUSE)
    app.carattere.aggiornato = None                                # cosi' la richiesta settimanale parte
    app.mem["tormentoni"] = {"ti voglio tanto bene": coinquilino.date.today().isoformat()}
    app.remember("è tornato a casa: Zio Mario")
    reqs = {r["kind"]: r["params"]["messages"][0]["content"] for r in app._night_requests()}
    assert "non i conteggi degli aerei" in reqs["carattere"] and "«ti voglio tanto bene»" in reqs["carattere"]
    assert "le fa Home Assistant" in reqs["idee"] and "Niente controlli sulle persone" in reqs["idee"]


def test_more_sad_news_and_all_saints():
    import feste
    from datetime import date
    assert coinquilino.Coinquilino._sad("Gli Stati Uniti vogliono espellere oltre 150 afghani: "
                                        "alcuni rischiano persecuzioni dai talebani")
    assert feste.festa_di(date(2026, 11, 1), {}, None)[1].startswith("Ognissanti")
