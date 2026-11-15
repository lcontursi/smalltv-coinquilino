"""La 3.4: celle e widget per le schermate a tutto cubo, schermata delle batterie e del termostato
(compaiono solo quando servono)."""
from conftest import STATES
from test_app import DAY

import coinquilino
import grafici

PIENO = (grafici.FULL_W, grafici.FULL_H)       # 3.4 (DC): 220x180, nella cornice delle foto


def bat(nome, valore, dc="battery"):
    return {"state": str(valore), "attributes": {"device_class": dc, "friendly_name": nome}}


def clima(stato="heat", attuale=21.5, goal=22, azione="heating", umid=58):
    return {"state": stato, "attributes": {"current_temperature": attuale, "temperature": goal,
                                           "hvac_action": azione, "current_humidity": umid,
                                           "friendly_name": "Soggiorno"}}


# ------------------------------------------------------------------ celle e widget
def test_grid_cells_stay_inside_and_do_not_overlap():
    for n in range(1, 9):
        celle = grafici.griglia(n)
        assert len(celle) == n
        for c in celle:
            assert c.x >= 0 and c.y >= 28 and c.x + c.w <= grafici.FULL_W and c.y + c.h <= grafici.FULL_H
        for i, a in enumerate(celle):
            for b in celle[i + 1:]:
                assert a.x + a.w <= b.x + 0.01 or b.x + b.w <= a.x + 0.01 or \
                    a.y + a.h <= b.y + 0.01 or b.y + b.h <= a.y + 0.01
    assert grafici.griglia(0) == []


def test_grid_columns_and_centered_last_row():
    assert len({round(c.y) for c in grafici.griglia(4)}) == 2             # 4 = 2x2
    assert len({round(c.y) for c in grafici.griglia(3)}) == 1             # 3 in fila
    cinque = grafici.griglia(5)                                           # 3 + 2: la seconda riga al centro
    assert cinque[3].x > cinque[0].x and abs((cinque[3].cx + cinque[4].cx) / 2 - grafici.FULL_W / 2) < 0.5


def test_level_colours():
    assert grafici.colore_livello(5) == grafici.RED and grafici.colore_livello(30) == grafici.YELLOW
    assert grafici.colore_livello(80) == grafici.GREEN


def test_battery_screen_draws_for_every_count(make_app, cube):
    font = make_app(dict(DAY, host=cube.host)).font_path
    for n in (1, 2, 5, 8, 11):
        img = grafici.schermata_batterie([(f"Dispositivo molto lungo {k}", k * 9) for k in range(n)], font)
        assert img.size == PIENO


def test_thermostat_screen_draws_with_and_without_extras(make_app, cube):
    font = make_app(dict(DAY, host=cube.host)).font_path
    assert grafici.schermata_termostato(21.5, 22, "heating", 58, [("Studio", 20.0)] * 3, font).size == PIENO
    assert grafici.schermata_termostato(18, None, None, None, [], font).size == PIENO


# ------------------------------------------------------------------ batterie
def test_battery_screen_only_when_something_is_low(make_app, cube):
    states = dict(STATES, **{"sensor.tel_luca": bat("Luca Rossi Battery level", 65),
                             "sensor.citofono": bat("Citofono batteria", 18),
                             "sensor.temperatura": bat("Sensore temperatura", "unavailable"),
                             "sensor.altro": {"state": "50", "attributes": {"device_class": "temperature"}}})
    app = make_app(dict(DAY, host=cube.host), states=states)
    assert app._batterie() == [("Citofono", 18.0), ("Luca", 65.0)]        # niente non-batterie, niente "unavailable"
    text, img = app._f_schermo_batterie()
    assert text == "Batteria bassa: Citofono al 18%." and img.size == PIENO
    states["sensor.citofono"]["state"] = "75"
    assert app._f_schermo_batterie() is None                              # tutto carico: la schermata non serve


def test_battery_screen_threshold_and_always_mode(make_app, cube):
    states = dict(STATES, **{"sensor.a": bat("Anna Battery level", 12), "sensor.b": bat("Bruno Battery level", 25),
                             "sensor.c": bat("Carla Battery level", 90)})
    app = make_app(dict(DAY, host=cube.host), states=states)
    assert app._f_schermo_batterie()[0] == "Batterie basse: Anna al 12%, Bruno al 25%."
    app.battery_below = 20
    assert app._f_schermo_batterie()[0] == "Batteria bassa: Anna al 12%."
    app.battery_below = 0                                                 # sempre, a turno
    states["sensor.a"]["state"], states["sensor.b"]["state"] = "60", "70"
    assert app._f_schermo_batterie()[0] == "Batterie: la più scarica è Anna, al 60%."


def test_battery_entities_option_and_same_names(make_app, cube):
    states = dict(STATES, **{"sensor.x1": bat("Luca Rossi Battery level", 10),
                             "sensor.x2": bat("Luca Bianchi Battery level", 15),
                             "sensor.fuori": bat("Altro", 5)})
    app = make_app(dict(DAY, host=cube.host, battery_entities=["sensor.x1", "sensor.x2"]), states=states)
    assert app._batterie() == [("Luca Rossi", 10.0), ("Luca Bianchi", 15.0)]     # due "Luca": nome intero
    assert app.battery_ents == ["sensor.x1", "sensor.x2"]


def test_battery_screen_in_the_rotation(make_app, cube):
    states = dict(STATES, **{"sensor.citofono": bat("Citofono batteria", 9)})
    app = make_app(dict(DAY, host=cube.host, talk_every_minutes=0), states=states)
    app.filler_order = ["schermo_batterie"]
    app._filler({})
    assert app.msg["screen"].size == PIENO and "Citofono al 9%" in app.msg["text"]
    assert coinquilino.TOPIC["schermo_batterie"] == "screen.battery"


# ------------------------------------------------------------------ termostato
def test_thermostat_screen_when_heating(make_app, cube):
    states = dict(STATES, **{"climate.soggiorno": clima(),
                             "sensor.studio": {"state": "20.4", "attributes": {"friendly_name": "Temperatura studio"}}})
    app = make_app(dict(DAY, host=cube.host, indoor_temperature=["climate.soggiorno", "sensor.studio"]),
                   states=states)
    text, img = app._f_schermo_termostato()
    assert text == "Termostato: 21,5 gradi, impostato a 22, sta riscaldando." and img.size == PIENO
    states["climate.soggiorno"]["attributes"]["hvac_action"] = "idle"
    assert app._f_schermo_termostato()[0] == "Termostato: 21,5 gradi, impostato a 22."


def test_thermostat_screen_off_or_missing(make_app, cube):
    app = make_app(dict(DAY, host=cube.host), states=dict(STATES))
    assert app._f_schermo_termostato() is None                            # nessun climate
    states = dict(STATES, **{"climate.soggiorno": clima(stato="off", azione="off")})
    app = make_app(dict(DAY, host=cube.host), states=states, name="spento")
    assert app._f_schermo_termostato() is None                            # spento: non si mostra
    states["climate.soggiorno"]["state"] = "unavailable"
    assert app._f_schermo_termostato() is None


def test_thermostat_option_picks_the_entity(make_app, cube):
    states = dict(STATES, **{"climate.a": clima(attuale=19), "climate.b": clima(attuale=23, goal=None, azione=None)})
    app = make_app(dict(DAY, host=cube.host, thermostat="climate.b"), states=states)
    assert app._f_schermo_termostato()[0] == "Termostato: 23 gradi."
    app2 = make_app(dict(DAY, host=cube.host), states=states, name="primo")
    assert app2._thermostat_entity() == "climate.a"
    ir = {"state": "cool", "attributes": {"current_temperature": 25}}             # condizionatore a infrarossi
    app3 = make_app(dict(DAY, host=cube.host), states=dict(STATES, **{"climate.aaa_ir": ir, "climate.z": clima()}),
                    name="vero")
    assert app3._thermostat_entity() == "climate.z"


def test_battery_names_keep_their_case():
    nome = coinquilino.Coinquilino._battery_name
    assert nome("sensor.x", "iPhone di Luca Battery level") == "iPhone"
    assert nome("sensor.x", "iPhone di Luca Battery level", intero=True)         == "iPhone Luca"
    assert nome("sensor.salotto_citofono_batteria", None) == "Salotto"


def test_thermostat_screen_in_the_rotation(make_app, cube):
    states = dict(STATES, **{"climate.soggiorno": clima()})
    app = make_app(dict(DAY, host=cube.host, talk_every_minutes=0), states=states)
    app.filler_order = ["schermo_termostato"]
    app._filler({})
    assert app.msg["screen"].size == PIENO and "sta riscaldando" in app.msg["text"]


# ------------------------------------------------------------------ bordo delle schermate (DC)
def test_screen_goes_in_the_photo_frame(make_app, cube):
    states = dict(STATES, **{"sensor.citofono": bat("Citofono batteria", 9)})
    app = make_app(dict(DAY, host=cube.host, talk_every_minutes=0), states=states)
    app.filler_order = ["schermo_batterie"]
    app._filler({})
    app._tick({})
    framed = app.msg["screen_frame"]
    assert framed.size == (240, 200) and app.msg["screen"].size == PIENO
    assert framed.getpixel((120, 100)) == app.msg["screen"].getpixel((110, 90))   # la schermata e' al centro
    app._tick({})
    assert app.msg["screen_frame"] is framed                                      # composta una volta sola
