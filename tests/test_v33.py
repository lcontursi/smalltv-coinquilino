"""La 3.3: i fotogrammi della cameretta si disegnano una volta sola per scena (CY), perche'
coinquilino teneva la CPU del NUC sempre sveglia ridisegnando ogni secondo."""
from PIL import Image

import alessio
from test_app import DAY


def contatore(monkeypatch, quadri=10):
    """Un render finto e veloce: cambia solo ogni `quadri` fotogrammi, come Alessio fermo."""
    calls = []

    def render(mood, sky, weather, text, frame, *a, **k):
        calls.append((mood, frame))
        return Image.new("RGB", (240, 200), (frame // quadri, len(mood), 0))

    monkeypatch.setattr(alessio, "render", render)
    monkeypatch.setattr(alessio, "render_base", render)          # 3.6 (DK): con la frase
    monkeypatch.setattr(alessio, "bubble", lambda img, *a, **k: img.copy())
    return calls


def giro(app, n=252, mood="happy", page=""):
    for f in range(n):
        app.frame = f
        app._render(mood, "day", "sunny", page, False, False, None, False, {})


def test_still_scene_is_drawn_once_per_loop(make_app, cube, monkeypatch):
    calls = contatore(monkeypatch)
    app = make_app(dict(DAY, host=cube.host))
    giro(app)
    assert len(calls) == 252
    giro(app)
    giro(app)
    assert len(calls) == 252                         # il secondo e il terzo giro sono gratis


def test_any_change_redraws(make_app, cube, monkeypatch):
    calls = contatore(monkeypatch)
    app = make_app(dict(DAY, host=cube.host))
    giro(app, 5)
    giro(app, 5, mood="sad")
    giro(app, 5, page="Ciao!")
    monkeypatch.setattr(alessio, "AGE", alessio.AGE + 1)
    giro(app, 5)
    assert len(calls) == 20 and calls[5][0] == "sad"
    giro(app, 5)
    assert len(calls) == 20


def test_same_frames_share_one_image(make_app, cube, monkeypatch):
    contatore(monkeypatch)
    app = make_app(dict(DAY, host=cube.host))
    giro(app, 30)
    cache = app._frames[1]
    assert cache[1] is cache[0] and cache[9] is cache[0] and cache[10] is not cache[0]
    assert len({id(i) for i in cache.values()}) == 3


def test_tick_uses_the_cache(make_app, cube, monkeypatch):
    calls = contatore(monkeypatch)
    app = make_app(dict(DAY, host=cube.host))
    for _ in range(2):
        app.frame, app.next_at, app.screen = 251, 0, None     # stesso fotogramma due volte
        app._tick({})
    assert len(calls) == 1 and len(cube.frames) == 2


def test_real_render_is_cached_and_identical(make_app, cube):
    app = make_app(dict(DAY, host=cube.host))
    app.frame = 3
    a = app._render("happy", "day", "sunny", "", False, False, None, False, {})
    b = alessio.render("happy", "day", "sunny", "", 3, False, False, seed=7, font_path=app.font_path,
                       festa=None, plane=False)
    assert a.tobytes() == b.tobytes()


# ------------------------------------------------------------------ 3.3.1
def test_blackboard_frames_are_cached_too(make_app, cube, monkeypatch):
    calls = []

    def render_card(card, mood, sky, weather, text, frame, *a, **k):
        calls.append(frame)
        return Image.new("RGB", (240, 200), (frame // 10, 0, 0))

    monkeypatch.setattr(alessio, "render_card", render_card)
    app = make_app(dict(DAY, host=cube.host))
    card = Image.new("RGB", (196, 128))
    for _ in range(2):
        for f in range(20):
            app.frame = f
            app._render("happy", "day", "sunny", "", False, False, None, None, {}, card=(card, 1.0))
    assert len(calls) == 12                          # 3.3.2: la lavagnetta gira su 12 fotogrammi
    app._render("happy", "day", "sunny", "", False, False, None, None, {},
                card=(Image.new("RGB", (196, 128)), 2.0))   # un'altra lavagnetta: si ridisegna
    assert len(calls) == 13


def test_tick_shows_the_blackboard_from_cache(make_app, cube, monkeypatch):
    calls = []
    real = alessio.render_card

    def render_card(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(alessio, "render_card", render_card)
    app = make_app(dict(DAY, host=cube.host))
    app._say_now("Guarda il grafico!", "say", card=Image.new("RGB", (196, 128), (9, 9, 9)))
    for _ in range(2):
        app.frame, app.next_at, app.screen = 251, 0, None
        app._tick({})
    assert len(calls) == 1 and len(cube.frames) == 2


def test_cube_uses_one_session(make_app, cube, monkeypatch):
    import coinquilino
    monkeypatch.setattr(coinquilino.requests, "get", lambda *a, **k: 1 / 0)    # mai una connessione nuova
    monkeypatch.setattr(coinquilino.requests, "post", lambda *a, **k: 1 / 0)
    app = make_app(dict(DAY, host=cube.host))
    for _ in range(3):
        app.next_at = 0
        app._tick({})
    assert len(cube.frames) >= 1 and app.fail == 0


# ------------------------------------------------------------------ 3.3.2
def test_a_sentence_loops_on_twelve_frames(make_app, cube, monkeypatch):
    calls = contatore(monkeypatch, quadri=1)          # parlando ogni fotogramma e' diverso
    app = make_app(dict(DAY, host=cube.host))
    giro(app, 120, page="Fuori ci sono 16 gradi.")
    assert sorted({f for _, f in calls}) == list(range(12)) and len(calls) == 12
    giro(app, 30)                                     # finita la frase: di nuovo il giro lungo
    assert len(calls) == 42


def test_twelve_keeps_mouth_lights_and_blink():
    assert all(12 % n == 0 for n in (2, 3, 4)) and any(f % 11 == 10 for f in range(12))
