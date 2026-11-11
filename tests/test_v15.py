"""La 1.5: Alessio comanda la casa dalla chat (lista bianca, conferme, log ACT)."""
import casa
import coinquilino
from conftest import STATES
from test_app import DAY, Resp

HOUSE = dict(STATES, **{
    "light.studio": {"state": "on", "attributes": {"friendly_name": "Luce studio"}},
    "light.ingresso": {"state": "off", "attributes": {"friendly_name": "Luce ingresso"}},
    "light.garage": {"state": "off", "attributes": {"friendly_name": "Garage"}},
    "climate.salone": {"state": "heat", "attributes": {"friendly_name": "Salone", "temperature": 21,
                                                       "current_temperature": 20.5}},
    "sensor.studio_t": {"state": "19.4", "attributes": {"friendly_name": "Studio",
                                                         "device_class": "temperature"}},
})
CTL = dict(DAY, anthropic_api_key="k", control=["light.studio", "light.ingresso", "climate.*"],
           owner="Zio Mario", owner_entity="person.mario", control_verify_seconds=0.2)


def obey(app, refuse=()):
    """Come Home Assistant: i servizi cambiano davvero lo stato (tranne quelli in refuse, che
    come i condizionatori del 29/10 vengono rifiutati: AppDaemon lo scrive solo nel log)."""
    real = app.call_service

    def call(service, **kw):
        real(service, **kw)
        e = kw.get("entity_id")
        st = app.states.get(e)
        if service in refuse or st is None:
            return None
        st = app.states[e] = {"state": st["state"], "attributes": dict(st.get("attributes") or {})}
        if service.endswith("/turn_off"):
            st["state"] = "off"
        elif service.endswith("/turn_on"):
            st["state"] = "on" if e.startswith("light.") else "heat"
        elif service == "climate/set_hvac_mode":
            st["state"] = kw["hvac_mode"]
        elif service == "climate/set_temperature":
            st["attributes"]["temperature"] = kw["temperature"]
        return None
    app.call_service = call
    return app


class FakeTool:
    """Claude che risponde con lo strumento comanda_casa (o con una frase)."""

    def __init__(self, monkeypatch, azioni=None, frase="Fatto, zio!", text=None):
        self.calls = []
        real = coinquilino.requests.post

        def post(url, **kw):
            if url != coinquilino.API_URL:
                return real(url, **kw)
            self.calls.append(kw["json"])
            if text is not None:
                content = [{"type": "text", "text": text}]
            else:
                content = [{"type": "tool_use", "id": "t1", "name": "comanda_casa",
                            "input": {"azioni": azioni, "frase": frase}}]
            return Resp({"content": content, "stop_reason": "tool_use",
                         "usage": {"input_tokens": 2500, "output_tokens": 40}})
        monkeypatch.setattr(coinquilino.requests, "post", post)


def acts(app):
    return [(s, kw) for s, kw in app.services if s.startswith(("light/", "climate/"))]


# ------------------------------------------------------------------ casa.py
def test_whitelist_and_validation():
    allowed = casa.consentite(HOUSE, ["light.studio", "climate.*"])
    assert allowed == ["climate.salone", "light.studio"]
    ok, err = casa.prepara([{"entita": "light.studio", "cosa": "spegni"},
                            {"entita": "light.garage", "cosa": "accendi"},
                            {"entita": "climate.salone", "cosa": "temperatura", "gradi": 45},
                            {"entita": "climate.salone", "cosa": "temperatura", "gradi": 20.5}],
                           HOUSE, allowed)
    assert [(a.service, a.data()) for a in ok] == [
        ("light/turn_off", {"entity_id": "light.studio"}),
        ("climate/set_temperature", {"entity_id": "climate.salone", "temperature": 20.5})]
    assert len(err) == 2 and "light.garage" in err[0]
    assert casa.descrivi("climate.salone", HOUSE["climate.salone"]) == \
        "climate.salone «Salone»: acceso (heat), impostati 21°, in stanza 20.5°"


def test_confirm_rules_and_answers():
    luce = casa.Azione("light/turn_off", "light.studio", "spegnere Luce studio")
    clima = casa.Azione("climate/turn_off", "climate.salone", "spegnere Salone")
    assert not casa.serve_conferma([luce], {"climate"})
    assert casa.serve_conferma([clima], {"climate"})
    assert casa.serve_conferma([luce], {"climate"}, fuori_casa=True)
    assert casa.serve_conferma([luce] * 4, set())
    assert casa.risposta("Sì!") == "si" and casa.risposta("ok") == "si"
    assert casa.risposta("no grazie") == "no" and casa.risposta("che ore sono?") is None
    assert casa.risposta("sì, ma prima dimmi che tempo fa domani pomeriggio") is None


# ------------------------------------------------------------------ dalla chat
def test_chat_turns_light_off(make_app, cube, monkeypatch):
    fake = FakeTool(monkeypatch, [{"entita": "light.studio", "cosa": "spegni"}], "Spenta, zio!")
    app = obey(make_app(dict(CTL, host=cube.host), states=HOUSE))
    assert app._chat_reply("spegni la luce dello studio") == "Spenta, zio!"
    assert acts(app) == [("light/turn_off", {"entity_id": "light.studio"})]
    sent = fake.calls[0]
    assert sent["tools"][0]["name"] == "comanda_casa"
    body = sent["messages"][0]["content"]
    assert "light.studio «Luce studio»: accesa" in body and "light.garage" not in body.split("La casa")[1]
    assert "Studio 19.4°" in body
    assert any(m.startswith("ACT") and "light/turn_off light.studio" in m for _, m in app.logs)


def test_climate_needs_confirmation(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, [{"entita": "climate.salone", "cosa": "spegni"}])
    app = obey(make_app(dict(CTL, host=cube.host), states=HOUSE))
    assert app._chat_reply("spegni il clima") == "Devo spegnere Salone? Rispondimi sì o no."
    assert not acts(app)
    assert app._chat_reply("sì") == "Fatto, zio!"                 # la conferma e' gratis
    assert acts(app) == [("climate/turn_off", {"entity_id": "climate.salone"})]


def test_confirmation_can_be_refused_or_lapse(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, [{"entita": "climate.salone", "cosa": "spegni"}])
    app = obey(make_app(dict(CTL, host=cube.host), states=HOUSE))
    app._chat_reply("spegni il clima")
    assert app._chat_reply("no") == "Va bene, non faccio niente."
    app._chat_reply("spegni il clima")
    app.pending["t"] -= 600                                    # passati 10 minuti
    app._chat_reply("sì")
    assert not acts(app)                                       # scaduta: niente eseguito


def test_from_outside_everything_needs_confirmation(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, [{"entita": "light.studio", "cosa": "spegni"}])
    states = dict(HOUSE, **{"person.mario": {"state": "not_home", "attributes": {"friendly_name": "Mario"}}})
    app = obey(make_app(dict(CTL, host=cube.host), states=states))
    assert app._chat_reply("spegni la luce dello studio").startswith("Devo spegnere")


def test_not_allowed_entity_is_refused(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, [{"entita": "light.garage", "cosa": "accendi"}])
    app = obey(make_app(dict(CTL, host=cube.host), states=HOUSE))
    assert app._chat_reply("accendi il garage").startswith("Questo non posso farlo")
    assert not acts(app)


def test_no_tool_without_control_or_with_switch_off(make_app, cube, monkeypatch):
    fake = FakeTool(monkeypatch, text="<frase>In casa sono accese: Luce studio.</frase>")
    app = obey(make_app(dict(CTL, host=cube.host, control=[]), states=HOUSE))
    assert app._chat_reply("ho lasciato luci accese?") == "In casa sono accese: Luce studio."
    assert "tools" not in fake.calls[0] and "Luci accese adesso: Luce studio." in \
        fake.calls[0]["messages"][0]["content"]
    states = dict(HOUSE, **{"input_boolean.comandi": {"state": "off", "attributes": {}}})
    app = obey(make_app(dict(CTL, host=cube.host, control_switch="input_boolean.comandi"), states=states))
    app._chat_reply("spegni la luce")
    assert "tools" not in fake.calls[-1]


def test_cannot_command_flag(make_app, cube, monkeypatch):
    fake = FakeTool(monkeypatch, text="<frase>Ciao!</frase>")
    app = obey(make_app(dict(CTL, host=cube.host), states=HOUSE))
    app._chat_reply("spegni la luce", sender="Anna", can_command=False)
    assert "tools" not in fake.calls[0]


def test_reply_callback_gets_answer_and_confirm_flag(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, [{"entita": "climate.salone", "cosa": "spegni"}])
    app = obey(make_app(dict(CTL, host=cube.host), states=HOUSE))
    got = []
    app._chat_reply("spegni il clima", reply=lambda t, ask: got.append((t, ask)))
    assert got == [("Devo spegnere Salone? Rispondimi sì o no.", True)]


# ------------------------------------------------------------------ Telegram
class Now:
    """threading.Thread che esegue subito: i test non aspettano."""

    def __init__(self, target, args=(), kwargs=None, daemon=None):
        self.target, self.args, self.kwargs = target, args, kwargs or {}

    def start(self):
        self.target(*self.args, **self.kwargs)


TG = dict(CTL, telegram_chats={111: "Zio Mario", 222: "Anna"})


def sent(app):
    return [kw for s, kw in app.services if s == "telegram_bot/send_message"]


def tg_app(make_app, cube, monkeypatch, **kw):
    monkeypatch.setattr(coinquilino.threading, "Thread", Now)
    return obey(make_app(dict(TG, host=cube.host, **kw), states=HOUSE))


def test_telegram_chat_and_command_with_buttons(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, [{"entita": "climate.salone", "cosa": "spegni"}], "Spento!")
    app = tg_app(make_app, cube, monkeypatch)
    app._tg_bus("telegram_text", {"chat_id": 111, "text": "spegni il clima", "id": 5}, {})
    msg = sent(app)[-1]
    assert msg["chat_id"] == 111 and msg["message"].startswith("Devo spegnere Salone")
    assert msg["inline_keyboard"] == ["Sì:/si, No:/no"]
    app._tg_bus("telegram_callback", {"chat_id": 111, "data": "/si", "id": "cb1"}, {})
    assert acts(app) == [("climate/turn_off", {"entity_id": "climate.salone"})]
    assert sent(app)[-1]["message"] == "Spento!"
    assert ("telegram_bot/answer_callback_query", {"callback_query_id": "cb1", "message": "✓ Sì"}) in app.services
    edit = [kw for s, kw in app.services if s == "telegram_bot/edit_replymarkup"][-1]
    assert edit["inline_keyboard"] == ["✓ Sì:/fatto"]                 # i pulsanti diventano la scelta fatta
    app._tg_bus("telegram_callback", {"chat_id": 111, "data": "/si", "id": "cb9"}, {})
    assert len(acts(app)) == 1 and sent(app)[-1]["message"] == "Spento!"   # un secondo Sì non fa niente


def test_telegram_family_chats_but_cannot_command(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, text="<frase>Ciao Anna!</frase>")
    app = tg_app(make_app, cube, monkeypatch)
    app._tg_bus("telegram_text", {"chat_id": 222, "text": "spegni la luce", "id": 6}, {})
    assert sent(app)[-1] == {"chat_id": 222, "message": "Ciao Anna!"}


def test_telegram_unknown_chat_ignored_and_duplicates_once(make_app, cube, monkeypatch):
    fake = FakeTool(monkeypatch, text="<frase>Ciao!</frase>")
    app = tg_app(make_app, cube, monkeypatch, telegram_event="event.bot")
    app._tg_bus("telegram_text", {"chat_id": 999, "text": "ciao", "id": 1}, {})
    assert not fake.calls and any("non autorizzata" in m for _, m in app.logs)
    upd = {"chat_id": 111, "text": "ciao", "id": 7}
    app._tg_bus("telegram_text", upd, {})
    app._tg_entity("event.bot", "all", None, {"state": "x", "attributes": dict(upd, event_type="telegram_text")}, {})
    assert len(fake.calls) == 1                                   # dal bus e dall'entita': una volta


def test_telegram_replies_are_not_said_aloud(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, text="<frase>Ciao!</frase>")
    app = tg_app(make_app, cube, monkeypatch, voice_player="media_player.casa", voice_tts="tts.x")
    app._tg_bus("telegram_text", {"chat_id": 111, "text": "ciao", "id": 8}, {})
    assert not [s for s, _ in app.services if s == "tts/speak"]
    app._chat_reply("ciao")                                       # dalla plancia di casa: a voce
    assert [s for s, _ in app.services if s == "tts/speak"]


def test_notifications_go_to_telegram_with_feedback(make_app, cube, monkeypatch):
    app = tg_app(make_app, cube, monkeypatch, notify="notify.tel")
    app._notify("Pioggia tra un'ora e la finestra è aperta", kind="regista")
    msg = sent(app)[-1]
    assert msg["chat_id"] == 111 and msg["inline_keyboard"] == ["👍:/su 1, 👎:/giu 1"]
    assert not [s for s, _ in app.services if s == "notify/tel"]  # Telegram e' il canale principale
    app._tg_bus("telegram_callback", {"chat_id": 111, "data": "/su 1", "id": "cb2",
                                      "message": {"message_id": 55}}, {})
    for i in range(7):                                            # 31/10: premuto otto volte
        app._tg_bus("telegram_callback", {"chat_id": 111, "data": "/su 1", "id": f"cbx{i}"}, {})
    assert app.carattere.riscontro["regista"]["su"] == 1
    edit = [kw for s, kw in app.services if s == "telegram_bot/edit_replymarkup"][0]
    assert edit["message_id"] == 55 and edit["inline_keyboard"] == ["👍 Grazie!:/fatto"]


def test_start_command_is_free(make_app, cube, monkeypatch):
    fake = FakeTool(monkeypatch, text="<frase>x</frase>")
    app = tg_app(make_app, cube, monkeypatch)
    app._tg_bus("telegram_command", {"chat_id": 111, "command": "/start", "text": "/start", "id": 9}, {})
    assert sent(app)[-1]["message"].startswith("Ciao Zio Mario!") and not fake.calls


def test_real_home_assistant_event_shape(make_app, cube, monkeypatch):
    """Il telegram_text vero visto in Home Assistant il 29/10 (dati finti)."""
    FakeTool(monkeypatch, text="<frase>Ciao zio!</frase>")
    app = tg_app(make_app, cube, monkeypatch)
    app._tg_bus("telegram_text", {
        "id": 2, "chat_id": 111, "date": "2026-10-29T12:43:42+00:00", "message_thread_id": None,
        "text": "Ciao", "user_id": 111, "from_first": "Mario", "from_last": "R",
        "bot": {"config_entry_id": "01ABC", "id": 9, "first_name": "Alessio", "last_name": None,
                "username": "ha_alessio_bot"}}, {})
    assert sent(app)[-1] == {"chat_id": 111, "message": "Ciao zio!"}



# ------------------------------------------------------------------ 1.5.1: "fatto" solo se e' vero
def test_refused_command_is_not_reported_as_done(make_app, cube, monkeypatch):
    """29/10: il condizionatore ha rifiutato turn_off e Alessio ha detto 'Ho spento'."""
    FakeTool(monkeypatch, [{"entita": "light.studio", "cosa": "spegni"}], "Spenta!")
    app = obey(make_app(dict(CTL, host=cube.host), states=HOUSE), refuse={"light/turn_off"})
    assert app._chat_reply("spegni la luce dello studio").startswith("Non sono riuscito a spegnere Luce studio")
    assert not [m for _, m in app.logs if m.startswith("ACT")]
    assert any(m.startswith("SKIP") and "non è cambiato" in m for _, m in app.logs)


def test_climate_turn_off_falls_back_to_hvac_mode(make_app, cube, monkeypatch):
    states = dict(HOUSE, **{"climate.letto": {"state": "cool", "attributes": {
        "friendly_name": "Condizionatore Letto 1", "hvac_modes": ["off", "auto", "cool", "heat", "dry"],
        "supported_features": 393, "temperature": 25}}})
    FakeTool(monkeypatch, [{"entita": "climate.letto", "cosa": "spegni"}], "Spento!")
    app = obey(make_app(dict(CTL, host=cube.host, control_confirm=[]), states=states),
               refuse={"climate/turn_off"})
    assert app._chat_reply("spegni il condizionatore del letto") == "Spento!"
    assert ("climate/set_hvac_mode", {"entity_id": "climate.letto", "hvac_mode": "off"}) in app.services
    assert app.states["climate.letto"]["state"] == "off"


def test_climate_turn_on_uses_last_mode_or_requested_mode(make_app, cube, monkeypatch):
    states = dict(HOUSE, **{"climate.letto": {"state": "cool", "attributes": {
        "friendly_name": "Letto", "hvac_modes": ["off", "auto", "cool", "heat"]}}})
    FakeTool(monkeypatch, [{"entita": "climate.letto", "cosa": "accendi"}], "Acceso!")
    app = obey(make_app(dict(CTL, host=cube.host, control_confirm=[]), states=states),
               refuse={"climate/turn_on"})
    app._casa_dati()                                              # vede che era in cool
    app.states["climate.letto"] = {"state": "off", "attributes": states["climate.letto"]["attributes"]}
    assert app._chat_reply("accendi il letto") == "Acceso!"
    assert app.states["climate.letto"]["state"] == "cool"
    ok, err = casa.prepara([{"entita": "climate.letto", "cosa": "accendi", "modo": "caldo"}],
                           app.states, ["climate.letto"])
    assert ok[0].service == "climate/set_hvac_mode" and ok[0].extra == {"hvac_mode": "heat"}
    ok, err = casa.prepara([{"entita": "climate.letto", "cosa": "accendi", "modo": "deumidifica"}],
                           app.states, ["climate.letto"])
    assert not ok and "deumidifica" in err[0]


def test_service_result_failure_is_seen_immediately(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, [{"entita": "light.studio", "cosa": "spegni"}])
    app = make_app(dict(CTL, host=cube.host, control_verify_seconds=30), states=HOUSE)
    app.call_service = lambda s, **kw: {"success": False, "error": {"message": "Unable to turn off"}}
    t = __import__("time").time()
    assert app._chat_reply("spegni").startswith("Non sono riuscito")
    assert __import__("time").time() - t < 5                     # niente attesa inutile
    assert any("Unable to turn off" in m for _, m in app.logs)


def test_partial_success_says_both(make_app, cube, monkeypatch):
    FakeTool(monkeypatch, [{"entita": "light.studio", "cosa": "spegni"},
                           {"entita": "light.ingresso", "cosa": "accendi"}], "Fatto!")
    app = obey(make_app(dict(CTL, host=cube.host), states=HOUSE), refuse={"light/turn_on"})
    out = app._chat_reply("spegni lo studio e accendi l'ingresso")
    assert out.startswith("Ho spento Luce studio, ma non sono riuscito ad accendere Luce ingresso")


# ------------------------------------------------------------------ 1.5.1: zucca e tormentoni (dal log del 29-30/10)
REAL = ["Caro diario, oggi ho visto 31 aerei e ho avuto la zucca in testa! Zio Mario è tornato a casa "
        "alle dieci e un quarto, booo! Ti voglio tanto bene!",
        "Ciao Zio Mario! Bentornato a casa! Booo, ti ho visto arrivare, ti voglio tanto bene!",
        "Zio Mario! Spengo le luci del balcone, booo! Ti voglio tanto bene!",
        "Zio Mario! Stasera ho la zucca in testa e il campanile è tutto nero, booo! Ti voglio tanto bene!"]


def test_tics_found_in_real_lines():
    import mente
    t = mente.formule(REAL, ["Zio Mario", "Alessio"])
    assert "booo" in t and "ti voglio tanto bene" in t
    assert "zio mario" not in t


def test_tics_and_costume_leave_the_prompt(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, force_festa="halloween", owner="Zio Mario"))
    for line in REAL:
        app._say_now(line, "chat", cost="paid")
    ctx = " ".join(app._context())
    assert "«booo»" in ctx and "«ti voglio tanto bene»" in ctx
    assert "Come sei adesso" not in ctx                                    # costume tolto
    assert "Ne hai già parlato oggi" in ctx
    ctx = " ".join(app._context(chat_text="come sei vestito oggi?"))
    assert "zucca" in ctx.split("Come sei adesso:")[1].split(".")[0]       # se lo chiedono, si'


def test_director_news_is_not_read_again_by_chatter(make_app, cube):
    """30/10: il regista racconta il seminario alle 08:58, la chiacchiera lo rilegge alle 09:15."""
    app = make_app(dict(DAY, host=cube.host, city="Bologna"))
    app.recent_news.extend([
        ("Dalla città", "Educazione finanziaria a Bologna, un seminario del Rotary Club Bologna Est in Prefettura"),
        ("Il Post", "La BCE ha lasciato invariati i tassi d'interesse")])
    app._say_now("Zio Mario, a Bologna c'è una notizia di soldi! Un seminario per imparare a gestirli, "
                 "in Prefettura. Che bello!", "regista")
    assert [t for _, t in app._news_fresh()] == ["La BCE ha lasciato invariati i tassi d'interesse"]


def test_night_job_logs_tokens_and_empty_reason(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app._night_log("ricordi", {"usage": {"input_tokens": 3000, "output_tokens": 4000},
                               "stop_reason": "max_tokens"}, batch=True)
    app._apply_night("ricordi", "", "max_tokens")
    logs = [m for _, m in app.logs]
    assert any(m.startswith("CLAUDE") and "3000+4000" in m and "stop=max_tokens" in m for m in logs)
    assert any("tetto di token finito nel ragionamento" in m for m in logs)
    assert app._night_req("ricordi", ["x"], [], "</ricordi>")["params"]["max_tokens"] == 16000
