"""La 3.1: il regista a rotazione di argomenti (CU), le curiosita' con la foto (CT), i filtri
sulle frasi (CQ, CR, CS), i fatti della memoria che scadono e la cache della chat MCP (CP)."""
import io
import random
from datetime import date, datetime, timedelta

from PIL import Image

import coinquilino
import mente
from test_app import DAY, FakeClaude, Resp


def regista(app, topic):
    app._argomento = lambda: (topic, "i vulcani" if topic in ("curiosita", "domanda") else None)
    return app._ask_claude({"kind": "regista", "key": "x"})


def test_topics_rotate_with_daily_caps(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    random.seed(3)
    for _ in range(2):
        app._argomento_fatto("meteo", None)
    seen = {app._argomento()[0] for _ in range(200)}
    assert "meteo" not in seen and "curiosita" in seen          # meteo: 2 al giorno
    app2 = make_app(dict(DAY, host=cube.host, director_topics_max={"curiosita": 0}))
    assert all(app2._argomento()[0] != "curiosita" for _ in range(100))


def test_curiosity_themes_do_not_repeat(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, curiosities=["i vulcani", "gli squali"]))
    app._argomento = coinquilino.Coinquilino._argomento.__get__(app)
    app.mem["detto"]["argomenti"] = {"_data": date.today().isoformat(), "temi": ["i vulcani"],
                                     "notizia": 9, "meteo": 9, "casa": 9, "ricordo": 9, "domanda": 9}
    assert app._argomento() == ("curiosita", "gli squali")


def test_director_context_only_has_its_topic(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch, "<frase>Lo sapevi che le formiche non dormono mai davvero?</frase>")
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app.ricordi.add("Mario deve far riparare la moto da Franco")
    regista(app, "domanda")
    body = fake.calls[0]["json"]
    content = body["messages"][0]["content"]
    assert "i vulcani" in content and "Previsioni:" not in content
    assert "Franco" not in body["system"]                          # i ricordi solo per l'argomento ricordo
    regista(app, "ricordo")
    assert "Franco" in fake.calls[1]["json"]["system"]


def test_curiosity_gets_a_wikipedia_photo_and_returns_in_showcase(make_app, cube, monkeypatch):
    FakeClaude(monkeypatch, "<umore>happy</umore><frase>Il vulcano più alto del sistema solare è su "
                            "Marte!</frase><foto>Olympus Mons")
    buf = io.BytesIO()
    Image.new("RGB", (300, 200), (200, 80, 20)).save(buf, "PNG")
    asked = []

    def get(url, **kw):
        asked.append(url)
        if url.startswith(coinquilino.WIKI_SUMMARY):
            return Resp({"thumbnail": {"source": "https://upload.example/olympus.jpg"}})
        r = Resp({})
        r.content = buf.getvalue()
        return r
    monkeypatch.setattr(coinquilino.requests, "get", get)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app._argomento = lambda: ("curiosita", "i vulcani")
    app.add_fact("regista", key="k1")
    app.last_said = 0
    app._speak({})
    assert asked[0].endswith("Olympus_Mons")
    assert app.msg["card"].size == (162, 128)
    v = [x for x in app._vetrina()["voci"] if x["tipo"] == "curiosita"]
    assert v and v[0]["testo"].startswith("Il vulcano")


def test_skip_and_invented_numbers(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch, "<frase>SALTA</frase>")
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    assert regista(app, "notizia") is None
    assert app._argomenti_oggi()["notizia"] == 1                  # il turno conta comunque
    fake.answer = "<frase>Ciao Mario, fuori ci sono 12 gradi e c'è un pacco.</frase>"
    assert app._ask_claude({"kind": "arrive", "name": "Mario", "key": "person.mario"}) is None
    assert "non inventare pacchi" in fake.calls[-1]["json"]["messages"][0]["content"]


def test_sentence_filters(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch, "<frase>Zio Mario, il vento sale... no, aspetta: le raffiche!</frase>")
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", owner="Zio Mario"))
    assert regista(app, "domanda") is None                          # CQ
    fake.answer = "<frase>Zio Mario, la notizia più utile per oggi: riapre il museo.</frase>"
    assert regista(app, "domanda") == "Riapre il museo."            # nome e formula via
    adesso = datetime.now().replace(hour=17, minute=14)
    assert app._senza_ora("Oggi alle 17:14 le previsioni danno sole.", adesso) == "Oggi le previsioni danno sole."
    assert app._senza_ora("Il treno parte alle 20:30.", adesso) == "Il treno parte alle 20:30."


def test_old_facts_expire_but_habits_stay():
    oggi = date(2026, 11, 13)
    r = mente.Ricordi([{"testo": "Franco prende la moto.", "tipo": "fatto", "ultimo": "2026-11-01"},
                       {"testo": "Mario beve il caffè amaro.", "tipo": "abitudine", "ultimo": "2026-10-01"},
                       {"testo": "Domani c'è il dentista.", "tipo": "fatto",
                        "ultimo": (oggi - timedelta(days=2)).isoformat()}])
    assert r.scadi(oggi) == 1
    assert [x["testo"][:5] for x in r.items] == ["Mario", "Doman"]


def test_mcp_chat_caches_tools_and_system(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app._api("", ["ciao"], [], "chat", 100, tools=[{"name": "t", "input_schema": {"type": "object"}}])
    sysb = fake.calls[0]["json"]["system"]
    assert isinstance(sysb, list) and sysb[0]["cache_control"] == {"type": "ephemeral"}
    app._api("", ["ciao"], [], "chat", 100)
    assert isinstance(fake.calls[1]["json"]["system"], str)


# ------------------------------------------------------------------ 3.2: disegni a forme (CM)
FORME = ["sfondo celeste", "rett 0 85 160 120 verde", "poli marrone 30 85 80 20 130 85",
         "cerchio 80 14 8 arancione", "linea 80 20 70 60 arancione 3", "boh 1 2 3"]


def test_shapes_are_parsed_and_drawn():
    import grafici
    fs = grafici.forme(FORME)
    assert [f[0] for f in fs] == ["sfondo", "rett", "poli", "cerchio", "linea"]   # "boh" saltata
    img = grafici.disegno(FORME)
    assert img.size == (162, 128) and img.getpixel((81, 120))[1] > 150           # prato verde
    assert grafici.disegno(["..RR..", ".RRRR.", "..RR..", "......", "......", "......"]).size == (162, 128)


def test_drawing_uses_shapes_and_no_owner_name(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch, "<titolo>Zio Mario, ecco il mio vulcano</titolo><disegno>\n"
                                   + "\n".join(FORME))
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", owner="Zio Mario",
                        curiosities=["i vulcani"]))
    title, img = app._ask_drawing()
    assert title == "Ecco il mio vulcano" and img.size == (162, 128)
    body = fake.calls[0]["json"]
    assert "pennarelli" in body["system"] and "i vulcani" in body["messages"][0]["content"]
    assert app.drawing_kept[1][0] == "sfondo celeste"
    assert app._argomenti_oggi()["disegni"] == ["i vulcani"]
