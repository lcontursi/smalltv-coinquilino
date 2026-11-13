"""La 1.9: "dimentica gli aerei" abbassa davvero l'interesse, il riordino notturno non fa ricordi
dai comandi della chat, le idee che ripetono una funzione gia' fatta si scartano."""
import os

import coinquilino
import mente
from test_app import DAY
from test_v14 import FakeBatch, night_app

IDEA_VECCHIA = ("Zio Mario, ho notato che a volte la casa resta vuota con la luce accesa. Se succede per "
                "più di mezz'ora, ti scrivo un avviso su Telegram. Poi la spengo io, se mi dici di sì.")


# ------------------------------------------------------------------ interessi bloccati
def test_forget_names_an_interest_and_blocks_it(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    assert app.carattere.interessi["aerei"] == 5
    answer = app._chat_reply("dimentica gli aerei che passano sopra casa")
    assert "non parlo più di aerei" in answer
    assert "aerei" not in app.carattere.interessi and app.carattere.bloccati == ["aerei"]
    assert "Non parlare mai di: aerei." in app.carattere.prompt()
    assert any(m.startswith("ACT") and "interessi bloccati: aerei" in m for _, m in app.logs)


def test_blocked_interest_survives_weekly_job_and_restart(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._chat_reply("dimentica gli aerei")
    app._apply_night("carattere", '<carattere>{"tratti": {}, "interessi": {"aerei": 9, "mare": 4}}</carattere>')
    assert "aerei" not in app.carattere.interessi
    again = mente.Carattere(app.carattere.to_json())               # come dopo un riavvio
    assert again.bloccati == ["aerei"] and "aerei" not in again.interessi


def test_other_ways_to_say_it_and_undo(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    assert "non parlo più di aerei" in app._chat_reply("Alessio, non parlare più di aerei!")
    assert app.carattere.bloccati == ["aerei"]
    assert "non parlo più" not in app._chat_reply("dimentica gli aerei")      # gia' bloccato: non si ripete
    assert "riparlare" in app._chat_reply("puoi riparlare di aerei")
    assert app.carattere.bloccati == [] and app.carattere.interessi["aerei"] == 3
    assert "non avevo smesso" in app._chat_reply("puoi riparlare di moto")
    assert "non parlo più di moto" in app._chat_reply("smetti di parlare delle moto")


def test_forget_without_an_interest_keeps_the_old_answer(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._chat_reply("ricordati che il fantasmino è un amico")
    assert app._chat_reply("dimentica il fantasmino") == "Fatto, l'ho dimenticato."
    assert app.carattere.bloccati == []
    assert app._chat_reply("dimentica il panduro") == "Non mi ricordavo niente del genere!"


def test_forget_interest_also_drops_its_memories(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.ricordi.add("Conto gli aerei che passano sopra casa")
    answer = app._chat_reply("dimentica gli aerei")
    assert "Ho tolto anche i ricordi" in answer and app.ricordi.items == []


# ------------------------------------------------------------------ riordino notturno
def test_night_ignores_chat_commands(make_app, cube, monkeypatch):
    FakeBatch(monkeypatch)
    app = night_app(make_app, cube, monkeypatch)
    app._chat_reply("dimentica gli aerei che passano sopra casa")
    app._chat_reply("ricordami di chiamare la nonna alle 18")
    app._chat_reply("ma che cos'hai in testa?")
    reqs = {r["kind"]: r["params"]["messages"][0]["content"] for r in app._night_requests()}
    assert "ma che cos'hai in testa?" in reqs["ricordi"]
    assert "dimentica gli aerei" not in reqs["ricordi"] and "ricordami di chiamare" not in reqs["ricordi"]
    assert "Non si parla più di: aerei" in reqs["ricordi"]
    eventi = app.mem["giorni"][coinquilino.date.today().isoformat()]["eventi"]
    assert not any("dimentica" in e or "ricordami" in e for e in eventi)
    assert any("ma che cos'hai in testa?" in e for e in eventi)


# ------------------------------------------------------------------ idee gia' fatte
def test_idea_already_done_is_recognised():
    assert mente.idea_gia_fatta(IDEA_VECCHIA) == "spegne le luci a casa vuota"
    assert mente.idea_gia_fatta("Se la finestra resta aperta spengo il clima.") \
        == "spegne il clima con la finestra aperta"
    assert mente.idea_gia_fatta("Ogni domenica ti scrivo un riassunto della settimana.") \
        == "riassunto della settimana"
    assert mente.idea_gia_fatta("Posso controllare la temperatura del salotto e avvisarti se sale "
                                "sopra i 24 gradi.") is None
    assert mente.idea_gia_fatta("Quale stanza di casa preferisci?") is None


def test_idea_already_done_is_discarded(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app._apply_night("idee", f"<tipo>funzione</tipo><idea>{IDEA_VECCHIA}</idea>")
    assert not app.mem.get("proposte") and app.mem["idee_scartate"] == [IDEA_VECCHIA]
    assert any(m.startswith("SKIP") and "già fatta (spegne le luci a casa vuota)" in m for _, m in app.logs)
    # una funzione nuova e una domanda passano
    app._apply_night("idee", "<tipo>funzione</tipo><idea>Ti avviso se il salotto supera i 24 gradi.</idea>")
    app._apply_night("idee", "<tipo>domanda</tipo><idea>Le luci del balcone: le spengo io la sera?</idea>")
    assert [p["tipo"] for p in app.mem["proposte"]] == ["funzione", "domanda"]


def test_discarded_ideas_go_into_next_prompt(make_app, cube):
    app = make_app(dict(DAY, host=cube.host, telegram_chats={111: "Zio Mario"}, owner="Zio Mario"))
    app.mem["idee_scartate"] = [IDEA_VECCHIA]
    app.remember("è tornato a casa: Zio Mario")
    reqs = {r["kind"]: r["params"]["messages"][0]["content"] for r in app._night_requests()}
    assert "Scartate perché lo sai già fare" in reqs["idee"] and "la casa resta vuota" in reqs["idee"]


def test_version():
    import re
    pyproject = open(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml"), encoding="utf-8").read()
    assert coinquilino.VERSION == "3.2.0" == re.search(r'^version = "(.+)"', pyproject, re.M).group(1)
