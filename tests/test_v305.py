import time

import coinquilino

from test_app import DAY


def test_long_sentence_keeps_turning_pages(make_app, cube):
    """Una frase su piu' pagine resta show_minutes e le pagine girano (12/11, 09:15)."""
    app = make_app(dict(DAY, host=cube.host, show_minutes=20))
    long = app.char.wrap("Zio Luca, sabato arriva la pioggia dopo giorni asciutti, " * 4, app.font_path)
    assert len(long) > 1
    n = len(long)
    t0 = time.time() - (5 * 60 + 0.1)
    app.msg = {"pages": long, "t0": t0, "kind": "filler"}
    seen = set()
    for k in range(n):
        app.msg["t0"] = t0 - k * coinquilino.PAGE_SECS
        text, talking, _ = app._bubble()
        assert text and not talking
        seen.add(text)
    assert seen == set(long)
    app.msg["t0"] = time.time() - 21 * 60
    assert app._bubble()[0] == ""
