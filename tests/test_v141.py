"""La 1.4.1: niente ragionamento nascosto, niente ripetizioni, notte a glimmer, filtri."""
import time
from datetime import date, datetime

import coinquilino
import grafici
from conftest import STATES
from test_app import DAY, FakeClaude, Resp

NIGHT = {"night_start": 0, "night_end": 24}          # sempre notte


# ------------------------------------------------------------------ A, F: ragionamento spento
def test_quick_calls_disable_thinking(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    app._claude(["x"], [], "say")
    sent = fake.calls[0]["json"]
    assert sent["thinking"] == {"type": "disabled"} and sent["output_config"] == {"effort": "low"}


def test_thinking_can_be_left_on(make_app, cube, monkeypatch):
    fake = FakeClaude(monkeypatch)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", claude_thinking=True))
    app._claude(["x"], [], "say")
    assert "thinking" not in fake.calls[0]["json"]


def test_model_without_thinking_params_falls_back(make_app, cube, monkeypatch):
    calls = []

    def post(url, **kw):
        calls.append(kw["json"])
        if "thinking" in kw["json"]:
            r = Resp({})
            r.status_code, r.text = 400, '{"error":{"message":"thinking: unknown field"}}'
            return r
        return Resp({"content": [{"type": "text", "text": "<frase>Ciao!</frase>"}], "stop_reason": "end_turn",
                     "usage": {"input_tokens": 100, "output_tokens": 10}})
    monkeypatch.setattr(coinquilino.requests, "post", post)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    assert app._claude(["x"], [], "say")[0] == "Ciao!"
    assert app._claude(["x"], [], "say")[0] == "Ciao!"
    assert len(calls) == 3                                     # una volta sola il tentativo con thinking
    assert any("non accetta thinking" in m for _, m in app.logs)


def test_empty_drawing_says_tokens_ran_out(make_app, cube, monkeypatch):
    def post(url, **kw):
        return Resp({"content": [{"type": "thinking", "thinking": "..."}], "stop_reason": "max_tokens",
                     "usage": {"input_tokens": 1900, "output_tokens": 1200}})
    monkeypatch.setattr(coinquilino.requests, "post", post)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k"))
    assert app._ask_drawing() == (None, None)
    assert any("tetto di token finito" in m for _, m in app.logs)


# ------------------------------------------------------------------ B, H: chiacchiere senza ripetizioni
def test_headlines_not_repeated_within_three_hours(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.recent_news.extend([("Il Post", "Titolo uno"), ("Il Post", "Titolo due")])
    said = set()
    for _ in range(2):
        t = app._f_notizia()
        app._chatter_told(coinquilino.clean(app.T(t)))
        said.add(t)
    assert said == {"Il Post: Titolo uno", "Il Post: Titolo due"}
    assert app._f_notizia() is None                            # tutte gia' lette


def test_filler_skips_any_text_said_recently(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, cards=False))
    app.filler_order = ["meteo"]
    app._f_meteo = lambda: "Sempre la stessa frase."
    app._chatter_told("Sempre la stessa frase.")
    app._filler({})
    assert not app.msg or app.msg["text"] != "Sempre la stessa frase."


def test_news_said_as_event_is_not_chatter_again(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.recent_news.append(("Dalla città", "Arriva la sagra"))
    app._say_now("Dalla città: Arriva la sagra", "news")
    assert app._f_notizia() is None
    assert not [x for x in app._context(full=True) if "Arriva la sagra" in x and "non ancora" in x]


# ------------------------------------------------------------------ G: il regista non si ripete
def test_director_remembers_its_topics_across_restart(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    for i in range(12):                                        # tante altre frasi in mezzo
        app._say_now(f"Un aereo! Numero {i}.", "plane")
    app._say_now("Ho contato 12 aerei sopra casa!", "regista")
    for i in range(10):
        app._say_now(f"Ciao {i}!", "arrive")
    app._mem_save()
    app2 = make_app(dict(DAY, host=cube.host))
    ctx = " ".join(app2._context(full=True))
    assert "argomenti che hai già scelto tu oggi" in ctx and "Ho contato 12 aerei" in ctx


# ------------------------------------------------------------------ I: pubblicita' e titoli
def test_gambling_ads_and_title_words_are_skipped():
    feed = {"skip": ["necrologi", "nera"]}
    item = lambda t, cats=(): {"title": t, "desc": "", "cats": list(cats)}   # noqa: E731
    skip = coinquilino.Coinquilino._skip_news
    assert skip(item("Coin Strike: Hold and Win, come funziona la slot Playson"), feed)
    assert skip(item("Le tecnologie che influenzano il futuro dei casinò online"), feed)
    assert skip(item("Necrologi di oggi"), feed)
    assert skip(item("Qualcosa", ["cronaca nera"]), feed)
    assert not skip(item("Cenerentola al teatro Politeama"), feed)   # "nera" solo parola intera
    assert not skip(item("Notte della Moda al De Pace"), feed)


# ------------------------------------------------------------------ K: chi e' in casa
def test_people_chatter_ignores_gps_bounce(make_app, cube):
    states = dict(STATES, **{"person.mario": {"state": "not_home", "attributes": {"friendly_name": "Mario"}},
                             "person.anna": {"state": "home", "attributes": {"friendly_name": "Anna"}}})
    app = make_app(dict(DAY, host=cube.host, owner="Zio Mario", owner_entity="person.mario",
                        nicknames={"person.mario": "Zio Mario", "person.anna": "Anna"}), states=states)
    app.left_at["person.mario"] = time.time() - 60                # uscito un minuto fa
    assert "fuori" not in app._f_chi()
    app.left_at["person.mario"] = time.time() - 3600
    assert "{owner} è fuori" in app._f_chi()


# ------------------------------------------------------------------ M: dollari e costume
def test_dollars_italian_style():
    assert grafici.dollari(0.0123) == "0,01 $"
    assert grafici.dollari(2) == "2 $"
    assert grafici.dollari(2.5) == "2,50 $"
    assert grafici.dollari(0.004) == "meno di 0,01 $"


def test_costume_mentioned_once_a_day(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, force_festa="halloween"))
    ctx = lambda: " ".join(app._context())                         # noqa: E731
    assert "zucca" in ctx().split("Come sei adesso:")[1].split(".")[0]
    app._say_now("Guarda, ho la zucca in testa!", "arrive", cost="paid")
    assert "Come sei adesso" not in ctx()                         # 1.7: niente aspetto, se non chiesto
    app.states["person.anna"] = {"state": "home", "attributes": {"friendly_name": "Anna"}}
    assert "zucca" in ctx().split("Come sei adesso:")[1].split(".")[0]   # Anna non l'ha ancora sentito


# ------------------------------------------------------------------ E: di notte comanda glimmer
def test_night_hands_cube_to_glimmer_and_back(make_app, cube):
    app = make_app(dict(NIGHT, host=cube.host, night_clock="glimmer"))   # dalla 1.8 non e' il predefinito
    app._daily({})
    assert cube.channels[-1] == {"name": "Night"} and app.night_handed == "ok"
    n = len(cube.channels)
    app._say_now("Ciao Zio!", "chat")                          # risponde, ma il cubo resta su glimmer
    assert len(cube.channels) == n
    app.night_start, app.night_end = 0, 0                      # mattina
    app._daily({})
    assert cube.channels[-1]["name"] == "Pixel" and app.night_handed is None


def test_night_without_glimmer_night_face_keeps_alessio(make_app, cube):
    cube.missing.add("Night")
    app = make_app(dict(NIGHT, host=cube.host, night_clock="glimmer"))
    app._daily({})
    assert app.night_handed == "no"
    assert not [m for _, m in app.logs if "quadrante notturno" in m]   # il primo 404 puo' essere anticipo
    app.night_retry = 0
    app._daily({})
    assert [m for _, m in app.logs if "non mostra il quadrante notturno" in m]
    app._show_channel()
    assert cube.channels[-1]["name"] == "Pixel"


def test_night_clock_can_be_turned_off(make_app, cube):
    app = make_app(dict(NIGHT, host=cube.host, night_clock="off"))
    app._daily({})
    assert not cube.channels


# ------------------------------------------------------------------ C: recupero del lavoro notturno
def test_night_job_catch_up_is_logged(make_app, cube, monkeypatch):
    from test_v14 import FakeBatch

    class Late(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.combine(date.today(), datetime.min.time()).replace(hour=8, minute=47)
    FakeBatch(monkeypatch)
    monkeypatch.setattr(coinquilino, "datetime", Late)
    app = make_app(dict(DAY, host=cube.host, anthropic_api_key="k", night_job_at="03:30"))
    app.remember("è tornato a casa: Mario")
    app._night_job({})
    assert any("recupero della notte" in m for _, m in app.logs)


# ------------------------------------------------------------------ 1.5: N e O dal log del 29/10
def test_costume_words_match_real_lines(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, force_festa="halloween"))
    for line in ("Sono una zucchina spaventosa, uuuh!", "Ho la zucchina in testa, guarda guarda!",
                 "Io metto il cappuccio zucca e aspetto il sole!", "Sono un fantasmino, buu!"):
        app.mem["detto"].pop("costume", None)
        app._say_now(line, "chat", cost="paid")
        assert app._costume_said(), line


def test_violent_news_is_sad():
    assert coinquilino.Coinquilino._sad(
        "Chi partecipa alle proteste violente in Albania potrà essere punito con multe fino a 5.500 euro")
