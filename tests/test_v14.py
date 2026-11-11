"""La 1.4: aggiornamenti chiari, mente (ricordi, carattere, crescita, promemoria),
lavoro notturno in batch, autonomia, biberon delle API."""
import json
from datetime import date, datetime, timedelta

import coinquilino
import mente
from conftest import STATES
from test_app import DAY, FakeClaude, Resp

EMPTY = {k: v for k, v in STATES.items() if not k.startswith("person.")}
EMPTY["person.mario"] = {"state": "not_home", "attributes": {"friendly_name": "Mario"}}


def services(app, name):
    return [kw for s, kw in app.services if s == name]


# ------------------------------------------------------------------ chat: ricordati, dimentica, ricordami
def test_remember_and_forget_from_chat_without_claude(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app._chat_reply("Alessio, ricordati che Anna ha la verifica di storia venerdì")
    assert app.msg["text"].startswith("Me lo ricordo!")
    assert "Anna ha la verifica di storia venerdì." in app.persona_now()
    app._chat_reply("dimentica la verifica di storia")
    assert app.msg["text"] == "Fatto, l'ho dimenticato." and not app.ricordi.items
    assert not fake.calls                                         # tutto gratis


def test_reminder_is_said_and_sent_to_phone(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, notify="notify.mobile_app_tel", owner="Zio Mario"))
    app._chat_reply("ricordami di chiamare il meccanico tra 1 minuti")
    assert "ti ricordo: chiamare il meccanico" in app.msg["text"]
    assert len(app.mem["promemoria"]) == 1
    app.mem["promemoria"][0]["quando"] = (datetime.now() - timedelta(minutes=1)).isoformat(timespec="minutes")
    app._reminders({})
    assert app.msg["text"] == "Zio Mario, ti ricordo: chiamare il meccanico!"
    assert services(app, "notify/mobile_app_tel")[0]["message"] == app.msg["text"]
    assert not app.mem["promemoria"]


# ------------------------------------------------------------------ crescita e carattere
def test_grows_one_year_per_month_up_to_12(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, grow=True))          # dalla 2.0 la crescita va chiesta
    assert app.anni == 2 and "Hai 2 anni" in app.persona
    app.mem["nascita"] = (date.today() - timedelta(days=95)).isoformat()
    assert app.anni == 5 and "Hai 5 anni" in app.persona
    app._daily({})
    assert [f["text"] for f in app.queue if f["kind"] == "crescita"] == [
        "Sono diventato più grande: adesso ho 5 anni!"]
    app._daily({})
    assert len([f for f in app.queue if f["kind"] == "crescita"]) == 1     # una volta sola
    app.mem["nascita"] = "2000-01-01"
    assert app.anni == 12 and "ragazzino" in app.persona


def test_bandit_does_not_grow(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, character="bandit"))
    assert app.anni is None and "Hai" not in app.persona


def test_feedback_buttons_and_drawing_gallery(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, feedback_up="input_button.su"))
    app.drawing_kept = ("Una zucca!", [".OO.", "OOOO"])
    app._say_now("Una zucca!", "disegno")
    app._feedback("input_button.su", "state", "2026-10-28T08:00", "2026-10-28T08:01", {"voce": "su"})
    assert app.carattere.riscontro["disegno"]["su"] == 1
    assert app.mem["galleria"][0]["titolo"] == "Una zucca!"
    text, card = app._f_galleria()
    assert "Una zucca!" in text and card is not None


def test_chat_reply_counts_as_appreciation(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._say_now("Lo sapevi che i polpi hanno tre cuori?", "fatto")
    app._chat_reply("davvero??")
    assert app.carattere.riscontro["fatto"]["risposte"] == 1


# ------------------------------------------------------------------ lavoro notturno (batch)
class FakeBatch:
    def __init__(self, monkeypatch, fail=False):
        self.created, self.fail = [], fail
        real_post, real_get = coinquilino.requests.post, coinquilino.requests.get
        out = {"ricordi": '<ricordi>[{"testo": "Zio Mario rientra verso le 19", "tipo": "abitudine"}]',
               "carattere": '<carattere>{"tratti": {"ironico": 9}, "interessi": {"aerei": 9}}</carattere>'
                            '<curiosita>["I polpi hanno tre cuori.", "Venere gira al contrario."]'}

        def post(url, **kw):
            if url == coinquilino.API_URL + "/batches":
                if self.fail:
                    raise coinquilino.requests.RequestException("batch non disponibile")
                self.created.append(kw["json"])
                return Resp({"id": "msgbatch_1", "processing_status": "in_progress"})
            if url == coinquilino.API_URL:
                kind = "ricordi" if "<ricordi>" in json.dumps(kw["json"]) else "carattere"
                return Resp({"content": [{"type": "text", "text": out[kind]}],
                             "usage": {"input_tokens": 3000, "output_tokens": 300}})
            return real_post(url, **kw)

        def get(url, **kw):
            if url == coinquilino.API_URL + "/batches/msgbatch_1":
                return Resp({"processing_status": "ended", "results_url": "https://x/results"})
            if url == "https://x/results":
                r = Resp({})
                r.text = "\n".join(json.dumps({"custom_id": k, "result": {"type": "succeeded", "message": {
                    "content": [{"type": "text", "text": v}],
                    "usage": {"input_tokens": 3000, "output_tokens": 300}}}}) for k, v in out.items())
                return r
            return real_get(url, **kw)
        monkeypatch.setattr(coinquilino.requests, "post", post)
        monkeypatch.setattr(coinquilino.requests, "get", get)


class Morning(datetime):
    """Le 4 di oggi: il lavoro notturno parte solo tra night_job_at e mezzogiorno."""
    @classmethod
    def now(cls, tz=None):
        return datetime.combine(date.today(), datetime.min.time()).replace(hour=4)


def night_app(make_app, cube, monkeypatch):
    monkeypatch.setattr(coinquilino, "datetime", Morning)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", night_job_at="00:00", owner="Zio Mario"))
    app.remember("è tornato a casa: Zio Mario")
    return app


def test_night_job_uses_batch_and_applies_results(make_app, cube, monkeypatch):
    fb = FakeBatch(monkeypatch)
    app = night_app(make_app, cube, monkeypatch)
    app._night_job({})
    kinds = [r["custom_id"] for r in fb.created[0]["requests"]]
    assert kinds == ["ricordi", "carattere"]                    # la prima volta anche il carattere
    assert app.mem["notte"]["batch"] == "msgbatch_1"
    app._night_job({})                                          # controlla il batch: finito
    assert [r["testo"] for r in app.ricordi.items] == ["Zio Mario rientra verso le 19"]
    assert app.carattere.tratti["ironico"] == 5                 # chiesto 9: un passo alla volta (4 -> 5)
    assert app.carattere.interessi["aerei"] == 7
    assert app.mem["curiosita"][0] == "I polpi hanno tre cuori."
    # costo a meta' prezzo: 2 x (3000 x 0,10 + 300 x 0,50) / 1e6 / 2
    assert abs(app.mem["api"]["speso"] - 2 * (3000 * 0.10 + 300 * 0.50) / 1e6 / 2) < 1e-12
    app._night_job({})
    assert len(fb.created) == 1                                 # una volta per notte


def test_night_job_falls_back_to_normal_calls(make_app, cube, monkeypatch):
    FakeBatch(monkeypatch, fail=True)
    app = night_app(make_app, cube, monkeypatch)
    app._night_job({})
    assert app.ricordi.items and "batch" not in app.mem["notte"]
    assert abs(app.mem["api"]["speso"] - 2 * (3000 * 0.10 + 300 * 0.50) / 1e6) < 1e-12   # prezzo pieno


# ------------------------------------------------------------------ autonomia
def lights(app, n=2):
    for i in range(n):
        app.states[f"light.l{i}"] = {"state": "on", "attributes": {"friendly_name": f"Luce {i}"}}


def test_director_can_send_a_notification(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch, "<avviso>Pioggia tra un'ora e la finestra dello studio è aperta</avviso>"
                                   "<umore>rain</umore><frase>Arriva la pioggia!")
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", autonomy=True, notify="notify.tel"))
    assert app._ask_claude({"kind": "regista", "key": "x"}) == "Arriva la pioggia!"
    assert "<avviso>" in fake.calls[0]["json"]["system"]
    assert services(app, "notify/tel")[0]["message"].startswith("Pioggia tra un'ora")
    assert not [m for lvl, m in app.logs if "prima di <frase>" in m]   # umore e avviso sono richiesti
    app._ask_claude({"kind": "regista", "key": "y"})
    assert len(services(app, "notify/tel")) == 1                 # al massimo uno ogni 3 ore


# ------------------------------------------------------------------ biberon delle API
def test_api_spending_sensor_and_budget_alert(make_app, cube, monkeypatch):
    FakeClaude(monkeypatch)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", api_budget_month=0.0005,
                        notify="notify.tel"))
    app._claude(["x"], [], "say")                                # 1834 in, 62 out
    one = (1834 * 0.10 + 62 * 0.50) / 1e6
    state, attrs = app.published["sensor.coinquilino_costo_api"]
    assert abs(state - round(one, 4)) < 1e-9 and attrs["chiamate"] == 1 and attrs["unit_of_measurement"] == "$"
    assert any(m.endswith(f"{one:.4f} $") for _, m in app.logs if m.startswith("CLAUDE"))
    app._claude(["x"], [], "say")
    app._claude(["x"], [], "say")                                # 3 x 0,000214 > 80% di 0,0005
    assert [f["kind"] for f in app.queue] == ["api_budget"]
    assert "budget delle API" in services(app, "notify/tel")[0]["message"]
    text, card = app._f_api()
    assert "meno di 0,01 $" in text


def test_cache_tokens_are_priced(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    cost = app._spend({"input_tokens": 100, "cache_read_input_tokens": 1000,
                       "cache_creation_input_tokens": 0, "output_tokens": 0}, "say")
    assert abs(cost - (100 + 100) * 0.10 / 1e6) < 1e-15


def test_mente_parser_edge_cases():
    now = datetime(2026, 10, 28, 22, 0)
    assert mente.comando("ricordami di uscire alle 7", now)[1] == datetime(2026, 10, 29, 7, 0)
    assert mente.comando("ricordami di bere alle 25", now)[0] == "promemoria?"
    assert mente.comando("Alessio come stai?", now) is None


def test_director_timer_still_works_after_a_drawing(make_app, cube, monkeypatch):
    FakeClaude(monkeypatch, "<titolo>Zucca</titolo><disegno>\n" + ".OOOOOO.\n" * 8)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", drawing_hours=0))
    app.last_random = 0
    app._random({})                                   # crea il turno del disegno
    app._speak({})
    app.last_random, app.msg, app.last_said = 0, None, 0
    app._random({})                                   # non deve rompersi (time - tuple)
    assert app.queue
