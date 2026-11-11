import aerei


def test_descrivi():
    a = {"flight": "RYR4LB", "type": "B738", "alt_m": 3200}
    assert aerei.descrivi(a, ("Brindisi", "Bergamo")) == \
        "un Boeing 737 Ryanair da Brindisi a Bergamo a 3.200 metri"
    assert aerei.descrivi({"flight": "IAM1234", "type": "C30J"}) == "un Hercules militare dell'Aeronautica Militare"
    assert aerei.descrivi({}) == "un aereo"


def test_compagnia_needs_icao_prefix():
    assert aerei.compagnia("EZY12") == "easyJet"
    assert aerei.compagnia("N123AB") is None
