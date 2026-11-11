from datetime import date

import feste


def test_pasqua_known_years():
    assert feste.pasqua(2025) == date(2025, 4, 20)
    assert feste.pasqua(2026) == date(2026, 4, 5)
    assert feste.pasqua(2027) == date(2027, 3, 28)


def test_feste_calendar():
    assert feste.festa_di(date(2026, 10, 31))[0] == "halloween"
    assert feste.festa_di(date(2026, 12, 25)) == ("natale", "Natale")
    assert feste.festa_di(date(2027, 1, 1))[0] == "capodanno"
    assert feste.festa_di(date(2026, 4, 6)) == ("pasqua", "Pasquetta")
    assert feste.festa_di(date(2026, 6, 15)) == (None, None)


def test_birthday_wins_and_patron():
    assert feste.festa_di(date(2026, 10, 31), {"10-31": "Anna"}) == ("compleanno", "il compleanno di Anna")
    patrono = {"from": "10-04", "to": "10-04", "name": "San Petronio"}
    assert feste.festa_di(date(2026, 10, 4), None, patrono) == ("patrono", "San Petronio")
    assert feste.festa_di(date(2026, 10, 5), None, patrono) == (None, None)
