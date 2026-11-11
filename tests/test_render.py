import os

import pytest
from conftest import FONTS

import alessio
import bandit
import grafici
from coinquilino import to_rgb565

FREDOKA = os.path.join(FONTS, "Fredoka.ttf")
SILK = os.path.join(FONTS, "Silkscreen-Regular.ttf")


@pytest.mark.parametrize("mood", ["happy", "sleep", "rain", "moto", "tired", "welcome"])
@pytest.mark.parametrize("festa", [None, "halloween", "natale", "capodanno", "compleanno", "pasqua", "patrono"])
def test_alessio_renders_every_mood_and_festa(mood, festa):
    img = alessio.render(mood, "day", None, "Ciao!", 3, True, False, font_path=FREDOKA, festa=festa)
    assert img.size == (240, 200) and img.mode == "RGB"


@pytest.mark.parametrize("mood", ["happy", "sleep", "rain", "moto", "tired", "welcome"])
def test_bandit_renders(mood):
    assert bandit.render(mood, "night", "rain", "", 1, font_path=SILK).size == (240, 200)


def test_cards():
    cards = [grafici.temperature([str(h) for h in range(12)], [20 - i * .5 for i in range(12)], [0] * 12, FREDOKA),
             grafici.claude(42, 31, FREDOKA),
             grafici.radar([{"dx": 1, "dy": 2}], FREDOKA),
             grafici.pixel_art(["KRK", "RKR"])]
    for c in cards:
        assert c.size == (grafici.CARD_W, grafici.CARD_H)
        assert alessio.render_card(c, text="guarda!", font_path=FREDOKA).size == (240, 200)


def test_rgb565_big_endian():
    from PIL import Image
    img = Image.new("RGB", (2, 1))
    img.putdata([(255, 0, 0), (0, 0, 255)])
    assert to_rgb565(img) == bytes([0xF8, 0x00, 0x00, 0x1F])
