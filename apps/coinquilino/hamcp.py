"""Client minimo per il server MCP di Home Assistant (integrazione "Model Context Protocol
Server", indirizzo /api/mcp, trasporto Streamable HTTP, token di lunga durata).

Home Assistant da' gli strumenti di Assist gia' filtrati sulle entita' esposte agli assistenti
vocali; Alessio li passa a Claude e decide lui cosa eseguire, cosa confermare e cosa scrivere nel
log. Niente chiamate a Claude qui dentro, e niente stato di Home Assistant oltre alla sessione MCP."""
import json
import time

import requests

PROTOCOL = "2025-03-26"
TOOLS_TTL = 600              # l'elenco degli strumenti si rilegge ogni 10 minuti


class McpError(Exception):
    pass


def _parse(r):
    """Risposta JSON oppure flusso SSE con un solo messaggio."""
    if "text/event-stream" in r.headers.get("content-type", ""):
        for line in r.text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:])
        return None
    return r.json() if r.text.strip() else None


class Client:
    def __init__(self, url, token, timeout=20, post=None):
        self.url = url
        self.token = token
        self.timeout = timeout
        self._post = post or requests.post
        self.session = None
        self._tools, self._tools_at = [], 0.0
        self._id = 0

    # ------------------------------------------------------------------ protocollo
    def _rpc(self, method, params=None, notify=False):
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            self._id += 1
            body["id"] = self._id
        h = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json",
             "Accept": "application/json, text/event-stream"}
        if self.session:
            h["Mcp-Session-Id"] = self.session
        r = self._post(self.url, headers=h, json=body, timeout=self.timeout)
        self.session = r.headers.get("Mcp-Session-Id") or self.session
        if r.status_code in (401, 403):
            raise McpError("il token non è accettato (serve un token di lunga durata valido)")
        if r.status_code == 404 and self.session:
            self.session = None                        # sessione scaduta: la si rifà
            raise McpError("sessione scaduta")
        if r.status_code >= 400:
            raise McpError(f"HTTP {r.status_code}: {r.text[:160]}")
        if notify:
            return None
        res = _parse(r) or {}
        if "error" in res:
            raise McpError(str(res["error"].get("message") or res["error"])[:160])
        return res.get("result") or {}

    def _start(self):
        if self.session:
            return
        self._rpc("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                 "clientInfo": {"name": "coinquilino", "version": "1"}})
        self._rpc("notifications/initialized", notify=True)

    def _call_rpc(self, method, params):
        """Con un secondo tentativo se la sessione e' scaduta."""
        for attempt in (1, 2):
            self._start()
            try:
                return self._rpc(method, params)
            except McpError as e:
                if attempt == 2 or str(e) != "sessione scaduta":
                    raise

    # ------------------------------------------------------------------ strumenti
    def tools(self):
        """Gli strumenti di Home Assistant (con un piccolo deposito di 10 minuti)."""
        if self._tools and time.time() - self._tools_at < TOOLS_TTL:
            return self._tools
        self._tools = self._call_rpc("tools/list", {}).get("tools") or []
        self._tools_at = time.time()
        return self._tools

    def read_only(self, name):
        t = next((t for t in self._tools if t.get("name") == name), None)
        return bool(t and (t.get("annotations") or {}).get("readOnlyHint"))

    def for_claude(self):
        """Gli strumenti nel formato dell'API di Anthropic."""
        return [{"name": t["name"], "description": (t.get("description") or "")[:1000],
                 "input_schema": t.get("inputSchema") or {"type": "object", "properties": {}}}
                for t in self.tools()]

    def call(self, name, args):
        """Esegue uno strumento -> (riuscito, testo, dati). dati e' il JSON della risposta se c'e'
        (per i comandi: {"data": {"success": [...], "failed": [...]}})."""
        res = self._call_rpc("tools/call", {"name": name, "arguments": args or {}})
        text = "".join(c.get("text", "") for c in res.get("content") or [] if c.get("type") == "text")
        try:
            data = json.loads(text)
        except ValueError:
            data = None
        return not res.get("isError"), text, data


def colpiti(data):
    """Dalla risposta di un comando: (riusciti, falliti) come liste di (nome, entity_id)."""
    d = (data or {}).get("data") or {}
    pick = lambda xs: [(x.get("name") or x.get("id") or "?", x.get("id")) for x in xs or []]   # noqa: E731
    return pick(d.get("success")), pick(d.get("failed"))
