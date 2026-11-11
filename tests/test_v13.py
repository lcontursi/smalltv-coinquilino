"""Le correzioni della 1.3 (dal log del 27/10/2026 sera)."""
from conftest import STATES
from test_app import DAY, FakeClaude


def arrive(app, entity, name):
    app.states[entity] = {"state": "home", "attributes": {"friendly_name": name}}
    app._person(entity, "state", "not_home", "home", {})


def test_arrivals_together_get_one_greeting_and_one_call(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch, "<frase>Bentornati tutti!</frase>")
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", owner="Zio Mario",
                        nicknames={"person.mario": "Zio Mario", "person.anna": "Zia Anna"}))
    arrive(app, "person.mario", "Mario")
    arrive(app, "person.anna", "Anna")
    assert not app.queue                                   # aspetta che arrivino tutti
    app._greet_arrivals({})
    assert [f["name"] for f in app.queue] == ["Zio Mario e Zia Anna"]
    app._speak({})
    assert len(fake.calls) == 1 and app.msg["text"] == "Bentornati tutti!"
    sent = fake.calls[0]["json"]["messages"][0]["content"]
    assert "salutale tutte" in sent and "Le persone: Zio Mario e Zia Anna" in sent


def test_single_arrival_still_addressed_personally(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    arrive(app, "person.anna", "Anna")
    app._greet_arrivals({})
    assert app._write(app.queue[0])[0] == "Ciao Anna, eccoti a casa."


def test_urgent_facts_keep_their_order(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.add_fact("regista", key="r")
    app.add_fact("arrive", name="Zio Mario", key="person.mario")
    app.add_fact("arrive", name="Anna", key="person.anna")
    assert [f.get("name") or f["kind"] for f in app.queue] == ["Zio Mario", "Anna", "regista"]


def test_claude_is_stopped_at_the_closing_tag(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch, "<umore>happy</umore><frase>Che bella giornata!")   # come con lo stop
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    text = app._ask_claude({"kind": "regista", "key": "x"})
    body = fake.calls[0]["json"]
    assert body["stop_sequences"] == ["</frase>"]
    assert "Prima della frase scrivi <umore>" in body["system"]
    assert text == "Che bella giornata!" and app.mood_tmp == "happy"


def test_text_before_the_tag_is_reported_once(make_app, cube, monkeypatch):
    FakeClaude(monkeypatch, "Ok, ecco una frase adatta al contesto di oggi, breve e tenera: <frase>Ciao!")
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app._claude(["x"], [], "say")
    app._claude(["x"], [], "say")
    warnings = [m for lvl, m in app.logs if lvl == "WARNING" and "prima di <frase>" in m]
    assert len(warnings) == 1 and "ecco una frase" in warnings[0]


def test_no_chatter_in_an_empty_house(make_app, cube):
    states = {k: v for k, v in STATES.items() if not k.startswith("person.")}
    states["person.anna"] = {"state": "not_home", "attributes": {"friendly_name": "Anna"}}
    app = make_app(dict(DAY, host=cube.host, talk_every_minutes=0), states=states)
    app._filler({})
    assert app.msg is None


def test_same_chatter_not_repeated_soon(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, talk_every_minutes=0))
    said = []
    for _ in range(30):
        app.msg, app.last_filler = None, 0
        app._filler({})
        if app.msg:
            said.append(app.msg["text"])
    assert said.count(next(t for t in said if t.startswith("Oggi è"))) == 1
    assert len(said) == len(set(said))                       # nessuna frase identica ripetuta


def test_claude_usage_needs_high_weekly(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    assert not app._claude_worth(16, 72) and app._claude_worth(16, 90) and app._claude_worth(55, 10)
