"""Test senza AppDaemon e senza rete: un finto Home Assistant e un finto cubo."""
import json
import os
import sys
import threading
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "apps", "coinquilino")
FONTS = os.path.join(APP, "fonts")
sys.path.insert(0, APP)


class FakeHass:
    """Il minimo di appdaemon.plugins.hass.hassapi.Hass che serve all'app."""

    def __init__(self, args=None, states=None, app_dir=".", name="coinquilino"):
        self.args, self.states, self.app_dir, self.name = dict(args or {}), dict(states or {}), app_dir, name
        self.logs, self.services, self.published = [], [], {}

    def get_state(self, entity=None, attribute=None):
        if "." not in entity:
            return {k: v for k, v in self.states.items() if k.startswith(entity + ".")}
        st = self.states.get(entity)
        if st is None:
            return None
        if attribute == "all":
            return st
        return st.get("attributes", {}).get(attribute) if attribute else st["state"]

    def listen_state(self, *a, **k): pass
    def listen_event(self, *a, **k): pass
    def run_every(self, *a, **k): pass
    def run_in(self, *a, **k): pass
    def log(self, msg, level="INFO"): self.logs.append((level, msg))
    def set_state(self, entity, state=None, attributes=None): self.published[entity] = (state, attributes)
    def call_service(self, service, **kw): self.services.append((service, kw))


hassapi = types.ModuleType("appdaemon.plugins.hass.hassapi")
hassapi.Hass = FakeHass
for name in ("appdaemon", "appdaemon.plugins", "appdaemon.plugins.hass"):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["appdaemon.plugins.hass.hassapi"] = hassapi


STATES = {
    "sun.sun": {"state": "above_horizon", "attributes": {"elevation": 30}},
    "zone.home": {"state": "0", "attributes": {"latitude": 44.49, "longitude": 11.34}},
    "weather.casa": {"state": "sunny", "attributes": {"temperature": 21}},
    "person.mario": {"state": "home", "attributes": {"friendly_name": "Mario"}},
    "person.anna": {"state": "not_home", "attributes": {"friendly_name": "Anna"}},
    "input_text.parla_con_alessio": {"state": "", "attributes": {}},
}


class Cube:
    """Finto cubo con il protocollo del canale Pixel."""

    def __init__(self):
        self.state = {"active": True, "seq": 1}
        self.frames, self.channels, self.auth = [], [], []
        self.token = None                                  # se impostato, come glimmer: Bearer <token>
        self.missing = set()                               # canali non attivi: /api/channel -> 404
        cube = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass

            def _ok(self, body=b'{"ok":true}', code=200):
                self.send_response(code)
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                self._ok(json.dumps(dict(cube.state, x=0, y=30, w=240, h=200, wait="")).encode())

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n)
                cube.auth.append(self.headers.get("Authorization"))
                path = urlparse(self.path)
                if cube.token and self.headers.get("Authorization") != f"Bearer {cube.token}":
                    return self._ok(b'{"error":"unauthorized"}', 401)
                if path.path == "/api/channel":
                    cube.channels.append(json.loads(body))
                    if json.loads(body).get("name") in cube.missing:
                        return self._ok(b'{"error":"no enabled channel with that name"}', 404)
                elif path.path == "/frame":
                    q = {k: int(v[0]) for k, v in parse_qs(path.query).items()}
                    cube.frames.append((q, len(body)))
                self._ok()

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.host = f"127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()


@pytest.fixture
def cube():
    c = Cube()
    yield c
    c.close()


@pytest.fixture
def make_app(tmp_path):
    """make_app(args, personal=dict|str|None, name=...) -> app inizializzata.
    Struttura come l'add-on: tmp/appdaemon.yaml, tmp/apps/ (app_dir)."""
    import yaml

    import coinquilino

    def make(args=None, personal=None, name="coinquilino", states=None):
        apps = tmp_path / "apps"
        apps.mkdir(exist_ok=True)
        if personal is not None:
            text = personal if isinstance(personal, str) else yaml.safe_dump(personal, allow_unicode=True)
            (tmp_path / "coinquilino_personale.yaml").write_text(text, encoding="utf-8")
        args = dict(args or {})
        args.setdefault("photo_dir", str(tmp_path / f"album_{name}"))       # mai in /media della macchina
        app = coinquilino.Coinquilino(args, states or STATES, apps, name)   # un Path, come AppDaemon 4.5
        app.initialize()
        return app

    return make
