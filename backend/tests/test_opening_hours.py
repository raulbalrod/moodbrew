from datetime import datetime

from app.services.maps_client import is_open_now

# 2026-07-29 es miercoles (We); 2026-08-01 es sabado (Sa)
_WED_10 = datetime(2026, 7, 29, 10, 0)
_WED_21 = datetime(2026, 7, 29, 21, 0)
_SAT_12 = datetime(2026, 8, 1, 12, 0)


def test_24_7():
    assert is_open_now("24/7", _WED_21) is True


def test_horario_laborable_abierto_y_cerrado():
    assert is_open_now("Mo-Fr 08:00-20:00", _WED_10) is True
    assert is_open_now("Mo-Fr 08:00-20:00", _WED_21) is False


def test_dia_sin_regla_es_desconocido():
    # Sabado no cubierto por la regla Mo-Fr -> desconocido (None), no se excluye
    assert is_open_now("Mo-Fr 08:00-20:00", _SAT_12) is None


def test_rangos_multiples_con_pausa():
    assert is_open_now("Mo-Fr 08:00-14:00,16:00-20:00", datetime(2026, 7, 29, 15, 0)) is False
    assert is_open_now("Mo-Fr 08:00-14:00,16:00-20:00", datetime(2026, 7, 29, 13, 0)) is True


def test_sin_dato_o_ilegible():
    assert is_open_now(None) is None
    assert is_open_now("") is None
    assert is_open_now("cuando me apetece") is None
