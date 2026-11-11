"""La 3.0: la chat comanda la casa con gli strumenti del server MCP di Home Assistant. Letture
subito, comandi con le nostre conferme, "fatto" solo dopo aver visto lo stato cambiare."""
import json

import coinquilino
import hamcp
from conftest import STATES
from test_app import DAY, Resp

TOOLS = [
    {"name": "homeassistant__GetLiveContext", "description": "stato della casa",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}},
     "annotations": {"readOnlyHint": True}},
    {"name": "intent__HassTurnOn", "description": "accende",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "area": {"type": "string"}}},
     "annotations": {"readOnlyHint": False}},
    {"name": "intent__HassTurnOff", "description": "spegne",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}},
     "annotations": {"readOnlyHint": False}},
    {"name": "climate__HassClimateSetTemperature", "description": "temperatura",
     "inputSchema": {"type": "object", "properties": {"temperature": {"type": "number"}}},
     "annotations": {"readOnlyHint": False}},
]


class FakeMcp:
    """Il server MCP di Home Assistant, finto: esegue sugli stati finti dell'app."""

    def __init__(self, app, entity="light.scrivania", nome="Luce Scrivania"):
        self.app, self.entity, self.nome, self.calls = app, entity, nome, []
        self._tools = TOOLS

    def tools(self):
        return TOOLS

    def for_claude(self):
        return [{"name": t["name"], "description": t["description"], "input_schema": t["inputSchema"]}
                for t in TOOLS]

    def read_only(self, name):
        return name == "homeassistant__GetLiveContext"

    def call(self, name, args):
        self.calls.append((name, args))
        if name == "homeassistant__GetLiveContext":
            if args.get("name") and args["name"] != self.nome:
                return True, '{{"error": "No exposed entities matched name {!r}"}}'.format(args["name"]), None
            return True, "- names: Luce Scrivania\n  domain: light\n  state: 'off'", None
        if args.get("name") and args["name"] != self.nome:
            return False, "Error calling tool: No entities matched the name", None
        if name.endswith("HassTurnOn") or name.endswith("HassTurnOff"):
            self.app.states[self.entity] = {"state": "on" if name.endswith("On") else "off", "attributes": {}}
        data = {"response_type": "action_done",
                "data": {"success": [{"name": self.nome, "id": self.entity}], "failed": []}}
        return True, json.dumps(data), data


class ScriptedClaude:
    """L'API Anthropic finta: risponde con le risposte in fila (strumenti o frasi)."""

    def __init__(self, monkeypatch, replies):
        self.replies, self.calls = list(replies), []
        real = coinquilino.requests.post

        def post(url, **kw):
            if url != coinquilino.API_URL:
                return real(url, **kw)
            self.calls.append(kw["json"])
            r = self.replies.pop(0)
            content = [{"type": "text", "text": r}] if isinstance(r, str) else \
                [{"type": "tool_use", "id": f"t{len(self.calls)}", "name": r[0], "input": r[1]}]
            return Resp({"content": content, "stop_reason": "tool_use" if not isinstance(r, str) else "end_turn",
                         "usage": {"input_tokens": 100, "output_tokens": 10}})
        monkeypatch.setattr(coinquilino.requests, "post", post)


def mcp_app(make_app, cube, **kw):
    states = dict(STATES, **{"light.scrivania": {"state": "off", "attributes": {"friendly_name": "Luce Scrivania"}}})
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", ha_mcp_url="http://ha/api/mcp",
                        ha_mcp_token="t", control_verify_seconds=0.2, **kw), states=states)
    app.mcp = FakeMcp(app)
    return app


def test_mcp_option_builds_the_client(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, ha_mcp_url="http://ha/api/mcp", ha_mcp_token="t"))
    assert isinstance(app.mcp, hamcp.Client) and app._control_on()
    app = make_app(dict(DAY, host=cube.host, ha_mcp_url="http://ha/api/mcp"))
    assert app.mcp is None and any("senza ha_mcp_token" in m for _, m in app.logs)


def test_chat_turns_on_a_light_through_mcp(make_app, cube, monkeypatch):
    app = mcp_app(make_app, cube)
    fake = ScriptedClaude(monkeypatch, [("intent__HassTurnOn", {"name": "Luce Scrivania"})])
    answer = app._chat_reply("accendi la luce della scrivania")
    assert answer == "Fatto: ho acceso Luce Scrivania."
    assert app.states["light.scrivania"]["state"] == "on"
    assert [t["name"] for t in fake.calls[0]["tools"]][0] == "homeassistant__GetLiveContext"
    assert any("HassTurnOn" in m and "light.scrivania" in m for _, m in app.logs)


def test_answer_keeps_the_short_name_for_the_next_command(make_app, cube, monkeypatch):
    """HA risponde con il nome lungo ("Presa lampada - Letto 3 Luce Scrivania"): nella chat deve
    restare il nome corto, se no il comando dopo ("spegnila") non trova piu' l'entita' (11/11)."""
    app = mcp_app(make_app, cube)
    app.mcp.nome_lungo = True
    real = app.mcp.call

    def long_name(name, args):
        ok, out, data = real(name, args)
        if data:
            data["data"]["success"][0]["name"] = "Presa lampada - Letto 3 Luce Scrivania"
        return ok, out, data
    app.mcp.call = long_name
    ScriptedClaude(monkeypatch, [("intent__HassTurnOn", {"name": "Luce Scrivania"})])
    answer = app._chat_reply("accendi la luce della scrivania")
    assert "Presa lampada" not in answer and "Luce Scrivania" in answer


def test_reads_first_then_answers(make_app, cube, monkeypatch):
    app = mcp_app(make_app, cube)
    fake = ScriptedClaude(monkeypatch, [("homeassistant__GetLiveContext", {"name": "Luce Scrivania"}),
                                        "<frase>La luce della scrivania è spenta.</frase>"])
    assert app._chat_reply("la luce della scrivania è accesa?") == "La luce della scrivania è spenta."
    second = fake.calls[1]["messages"]
    assert second[1]["role"] == "assistant" and second[2]["content"][0]["type"] == "tool_result"
    assert "state: 'off'" in second[2]["content"][0]["content"]


def test_climate_asks_for_confirmation(make_app, cube, monkeypatch):
    app = mcp_app(make_app, cube)
    ScriptedClaude(monkeypatch, [("climate__HassClimateSetTemperature", {"temperature": 20})])
    answer = app._chat_reply("metti 20 gradi")
    assert answer.startswith("Devo mettere la temperatura a 20 gradi") and app.pending["mcp"]
    assert not [c for c in app.mcp.calls if "Climate" in c[0]]
    done = app._chat_reply("sì")
    assert done.startswith("Fatto: ho regolato") and done.endswith("a 20 gradi.")
    assert app.mcp.calls[-1] == ("climate__HassClimateSetTemperature", {"temperature": 20})


def test_whole_area_or_from_outside_asks(make_app, cube, monkeypatch):
    app = mcp_app(make_app, cube)
    ScriptedClaude(monkeypatch, [("intent__HassTurnOff", {"area": "Salotto"})])
    assert app._chat_reply("spegni tutto il salotto").startswith("Devo spegnere")
    assert app._chat_reply("no") == "Va bene, non faccio niente." and not app.mcp.calls
    assert app._mcp_confirm([("intent__HassTurnOn", {"name": "Luce Scrivania"})], remote=True)


def test_wrong_name_goes_back_to_claude_and_nothing_runs(make_app, cube, monkeypatch):
    """Il nome lungo rimasto nella chat: Assist non lo trova. Claude riceve l'errore, rilegge e
    riprova con il nome giusto; il comando sbagliato non parte mai (11/11)."""
    app = mcp_app(make_app, cube)
    fake = ScriptedClaude(monkeypatch, [("intent__HassTurnOff", {"name": "Scrivania Anna"}),
                                        ("intent__HassTurnOff", {"name": "Luce Scrivania"})])
    assert app._chat_reply("spegnila") == "Fatto: ho spento Luce Scrivania."
    assert not any(c[0] == "intent__HassTurnOff" and c[1]["name"] == "Scrivania Anna" for c in app.mcp.calls)
    err = fake.calls[1]["messages"][-1]["content"][0]
    assert err["is_error"] and "Nomi simili: Luce Scrivania" in err["content"]


def test_unknown_device_after_retries(make_app, cube, monkeypatch):
    app = mcp_app(make_app, cube)
    ScriptedClaude(monkeypatch, [("intent__HassTurnOn", {"name": "Garage"})] * 4)
    assert app._chat_reply("accendi il garage") is not None
    assert not any(c[0] == "intent__HassTurnOn" for c in app.mcp.calls)


def test_done_only_if_the_state_changed(make_app, cube, monkeypatch):
    app = mcp_app(make_app, cube)
    real = app.mcp.call

    def lazy(name, args):                          # HA dice "fatto" ma la luce resta spenta
        ok, out, data = real(name, args)
        app.states["light.scrivania"]["state"] = "off"
        return ok, out, data
    app.mcp.call = lazy
    ScriptedClaude(monkeypatch, [("intent__HassTurnOn", {"name": "Luce Scrivania"})])
    assert app._chat_reply("accendi la luce della scrivania").startswith("Non sono riuscito")


def test_without_commanders_no_tools(make_app, cube, monkeypatch):
    app = mcp_app(make_app, cube)
    fake = ScriptedClaude(monkeypatch, ["<frase>Ciao.</frase>"])
    app._chat_reply("ciao", can_command=False)
    assert "tools" not in fake.calls[0] and not app.mcp.calls


# ------------------------------------------------------------------ il client MCP
class Http:
    def __init__(self, status, body, headers=None, sse=False):
        self.status_code, self.headers = status, dict(headers or {})
        self.headers["content-type"] = "text/event-stream" if sse else "application/json"
        self.text = ("event: message\ndata: " + json.dumps(body)) if sse else json.dumps(body) if body else ""

    def json(self):
        return json.loads(self.text)


def test_client_session_tools_and_call():
    sent = []

    def post(url, headers, json, timeout):
        sent.append((headers.get("Mcp-Session-Id"), json["method"]))
        m = json["method"]
        if m == "initialize":
            return Http(200, {"jsonrpc": "2.0", "id": 1, "result": {}}, {"Mcp-Session-Id": "abc"})
        if m == "notifications/initialized":
            return Http(202, None)
        if m == "tools/list":
            return Http(200, {"jsonrpc": "2.0", "id": 2, "result": {"tools": TOOLS}}, sse=True)
        data = {"data": {"success": [{"name": "Luce", "id": "light.x"}], "failed": []}}
        return Http(200, {"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text":
                                                                                __import__("json").dumps(data)}]}})
    c = hamcp.Client("http://ha/api/mcp", "tok", post=post)
    assert [t["name"] for t in c.for_claude()][1] == "intent__HassTurnOn"
    assert c.read_only("homeassistant__GetLiveContext") and not c.read_only("intent__HassTurnOn")
    ok, _, data = c.call("intent__HassTurnOn", {"name": "Luce"})
    assert ok and hamcp.colpiti(data) == ([("Luce", "light.x")], [])
    assert sent[0] == (None, "initialize") and sent[-1] == ("abc", "tools/call")


def test_client_bad_token():
    c = hamcp.Client("http://ha/api/mcp", "tok", post=lambda *a, **k: Http(401, {"x": 1}))
    try:
        c.tools()
        raise AssertionError("doveva fallire")
    except hamcp.McpError as e:
        assert "token" in str(e)


def test_long_name_is_fixed_without_asking_claude(make_app, cube, monkeypatch):
    """3.0.3: il nome lungo contiene quello vero: si corregge da soli, senza un altro giro."""
    app = mcp_app(make_app, cube)
    fake = ScriptedClaude(monkeypatch, [("intent__HassTurnOn", {"name": "Presa lampada - Letto 3 Luce Scrivania"})])
    assert app._chat_reply("accendila") == "Fatto: ho acceso Luce Scrivania."
    assert len(fake.calls) == 1 and app.states["light.scrivania"]["state"] == "on"


def test_pronoun_gets_the_last_command(make_app, cube, monkeypatch):
    """3.0.4: dopo "accendi la luce" il messaggio "spegnila" porta con se' l'ultimo comando."""
    app = mcp_app(make_app, cube)
    fake = ScriptedClaude(monkeypatch, [("intent__HassTurnOn", {"name": "Luce Scrivania"}),
                                        ("intent__HassTurnOff", {"name": "Luce Scrivania"})])
    app._chat_reply("accendi la luce della scrivania")
    assert app._chat_reply("spegnila") == "Fatto: ho spento Luce Scrivania."
    second = fake.calls[1]["messages"][0]["content"]
    assert "Ultimo comando fatto in casa" in second and "ho acceso Luce Scrivania" in second
    assert "spegnila" in fake.calls[1]["messages"][0]["content"] and "pronome" in second

