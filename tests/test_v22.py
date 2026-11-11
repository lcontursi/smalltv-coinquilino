"""La 2.2: le regole sulla casa stanno in Home Assistant (blueprint) e arrivano con l'evento
coinquilino_say; promemoria e appuntamenti dalle liste todo e dai calendari di HA."""
import time
from datetime import datetime, timedelta

import mente
from test_app import DAY
from test_v14 import services


def say(app, **data):
    app._say_event("coinquilino_say", data, {})


# ------------------------------------------------------------------ evento standard (CB)
def test_event_away_goes_to_the_phone_only(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, notify="notify.tel"))
    app.states["person.anna"]["state"] = "not_home"
    app.states["person.mario"] = {"state": "not_home", "attributes": {}}
    for e in [e for e in app.states if e.startswith("person.")]:
        app.states[e]["state"] = "not_home"
    say(app, text="Casa vuota ma sono rimaste accese: Cucina.", away="notify")
    assert services(app, "notify/tel")[0]["message"].startswith("Casa vuota")
    assert app.msg is None


def test_event_night_defer_and_key_once(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, notify="notify.tel", night_start=0, night_end=24))
    say(app, text="Alle 02:40 hanno suonato al citofono.", night="defer", key="citofono")
    say(app, text="Alle 02:40 hanno suonato al citofono.", night="defer", key="citofono")
    assert [r["text"] for r in app.mem["rimandati"]] == ["Alle 02:40 hanno suonato al citofono."]
    assert not services(app, "notify/tel")


def test_event_remember_quiet_and_arrival(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    say(app, remember="hanno suonato al citofono", quiet_seconds=60, expect_arrival=True)
    assert app.msg is None and app.quiet_until > time.time() + 50 and time.time() - app.open_at < 2
    day = app.mem["giorni"][datetime.now().date().isoformat()]["eventi"]
    assert day[-1].endswith("hanno suonato al citofono")


def test_event_wait_goes_in_the_queue(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    say(app, text="Batteria del sensore bagno al 12%.", wait=True)
    assert app.msg is None and app.queue[-1]["text"] == "Batteria del sensore bagno al 12%."


def test_old_rule_options_only_warn(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, doorbell="event.x", windows={"binary_sensor.f": "climate.c"}))
    assert sum("dalla 2.2 questa regola sta in Home Assistant" in m for _, m in app.logs) == 2
    assert not hasattr(app, "_autopilot") and not hasattr(app, "_doorbell_ring")
    assert mente.comando("domani aspetto un pacco") is None


# ------------------------------------------------------------------ agenda (CD)
def agenda_app(make_app, cube, responses, **kw):
    app = make_app(dict(DAY, host=cube.host, notify="notify.tel", reminders_todo="todo.alessio",
                        calendars=["calendar.famiglia"], **kw))

    def call(service, **data):
        app.services.append((service, data))
        if service in responses:
            return {"success": True, "result": {"response": {data["entity_id"]: responses[service]}}}
        return {"success": True}
    app.call_service = call
    return app


def test_todo_due_items_are_said_once(make_app, cube):
    past = (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S")
    app = agenda_app(make_app, cube, {"todo/get_items": {"items": [
        {"uid": "1", "summary": "Chiamare il dentista", "due": past, "status": "needs_action"},
        {"uid": "2", "summary": "Comprare il latte", "status": "needs_action"}]},
        "calendar/get_events": {"events": []}})
    app._agenda({})
    app._agenda({})
    said = [kw["message"] for kw in services(app, "notify/tel")]
    assert said == ["Zio, ti ricordo: Chiamare il dentista!"] or said[0].endswith("Chiamare il dentista!")
    assert len(said) == 1
    ctx = " ".join(app._context())
    assert "Nella lista delle cose da fare: " in ctx and "Comprare il latte" in ctx


def test_calendar_event_soon_is_announced(make_app, cube):
    start = (datetime.now() + timedelta(minutes=30)).astimezone().isoformat(timespec="seconds")
    app = agenda_app(make_app, cube, {"todo/get_items": {"items": []},
                                      "calendar/get_events": {"events": [{"summary": "Dentista", "start": start}]}})
    app._agenda({})
    msg = services(app, "notify/tel")[0]["message"]
    assert msg.startswith("Fra ") and "Dentista" in msg
    assert app._f_agenda().startswith("Oggi in agenda: ")


def test_chat_reminder_goes_to_the_todo_list_and_done(make_app, cube):
    app = agenda_app(make_app, cube, {"todo/get_items": {"items": [
        {"uid": "7", "summary": "Portare la moto dal meccanico", "status": "needs_action"}]},
        "calendar/get_events": {"events": []}})
    app._chat_command("ricordami di chiamare la nonna alle 18")
    add = services(app, "todo/add_item")[0]
    assert add["entity_id"] == "todo.alessio" and "nonna" in add["item"] and add["due_datetime"].endswith("18:00:00")
    assert not app.mem["promemoria"]
    app._agenda({})
    assert app._todo_done("fatto la moto dal meccanico") == "Segnato come fatto: Portare la moto dal meccanico."
    assert services(app, "todo/update_item")[0]["status"] == "completed"
    assert app._todo_done("fatto tutto bene oggi") is None


def test_workday_in_context(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, workday="binary_sensor.workday_sensor"))
    app.states["binary_sensor.workday_sensor"] = {"state": "off", "attributes": {}}
    assert "Oggi è un giorno festivo o di riposo." in app._context()


# ------------------------------------------------------------------ Siri / CarPlay (CC)
def test_chat_reply_also_on_the_phone(make_app, cube, monkeypatch):
    app = make_app(dict(DAY, host=cube.host, notify="notify.tel", chat_reply_phone=True,
                        chat_entity="input_text.parla_con_alessio"))
    started = []

    class T:
        def __init__(self, target, args, kwargs, daemon):
            started.append((target, args, kwargs))

        def start(self):
            target, args, kwargs = started[-1]
            target(*args, **kwargs)
    monkeypatch.setattr("coinquilino.threading.Thread", T)
    app.mem["ultimo_messaggio"] = time.time()
    app._chat("input_text.parla_con_alessio", "state", "", "ricordati che domani c'è il mercato", {})
    assert services(app, "notify/tel")[0]["message"].startswith("Me lo ricordo!")


# ------------------------------------------------------------------ blueprint
def test_blueprints_load_and_use_known_fields():
    import glob
    import os

    import yaml

    class L(yaml.SafeLoader):
        pass
    L.add_constructor("!input", lambda loader, node: f"<{loader.construct_scalar(node)}>")
    known = {"text", "about", "mood", "minutes", "telegram", "wait", "away", "night", "key",
             "repeat_hours", "remember", "quiet_seconds", "expect_arrival", "cube", "instance"}
    root = os.path.join(os.path.dirname(__file__), "..", "blueprints")
    files = glob.glob(os.path.join(root, "*", "coinquilino", "*.yaml"))
    assert len(files) == 8

    def events(x):
        if isinstance(x, dict):
            if x.get("event") == "coinquilino_say":
                yield x.get("event_data") or {}
            for v in x.values():
                yield from events(v)
        elif isinstance(x, list):
            for v in x:
                yield from events(v)
    for f in files:
        bp = yaml.load(open(f, encoding="utf-8"), Loader=L)
        assert bp["blueprint"]["domain"] in ("automation", "script")
        assert "lcontursi/smalltv-coinquilino" in bp["blueprint"]["source_url"]
        found = list(events(bp))
        assert found, f
        for data in found:
            assert set(data) <= known, (f, set(data) - known)
