from app.services.maps_client import (
    GeoapifyPlace,
    _is_bakery,
    _is_commodity_chain,
    _parse_place,
)


def test_parse_place_completo():
    feature = {
        "properties": {
            "name": "Toma Cafe",
            "formatted": "Calle de la Palma 49, Madrid",
            "city": "Madrid",
            "lat": 40.4265,
            "lon": -3.7075,
            "place_id": "abc123",
            "datasource": {
                "raw": {"opening_hours": "Mo-Fr 08:00-20:00", "internet_access": "wlan"}
            },
        }
    }
    place = _parse_place(feature)
    assert isinstance(place, GeoapifyPlace)
    assert place.name == "Toma Cafe"
    assert place.city == "Madrid"
    assert place.external_id == "abc123"
    assert place.opening_hours == "Mo-Fr 08:00-20:00"
    assert place.has_wifi is True


def test_parse_place_defaults():
    place = _parse_place({"properties": {"lat": 1.0, "lon": 2.0, "datasource": {}}})
    assert place.name == "Cafeteria sin nombre"
    assert place.has_wifi is False
    assert place.opening_hours is None


def test_is_commodity_chain_por_nombre():
    feature = {"properties": {"name": "Starbucks Sol"}}
    assert _is_commodity_chain(feature) is True


def test_is_commodity_chain_por_brand():
    feature = {"properties": {"name": "Cafe X", "datasource": {"raw": {"brand": "Costa Coffee"}}}}
    assert _is_commodity_chain(feature) is True


def test_especialidad_no_es_cadena():
    feature = {"properties": {"name": "Toma Cafe", "datasource": {"raw": {}}}}
    assert _is_commodity_chain(feature) is False


def test_is_bakery_por_shop():
    feature = {"properties": {"name": "Santa Gloria", "datasource": {"raw": {"shop": "bakery"}}}}
    assert _is_bakery(feature) is True


def test_is_bakery_por_nombre():
    feature = {"properties": {"name": "Horno Nueva Florida", "datasource": {"raw": {}}}}
    assert _is_bakery(feature) is True


def test_cafe_no_es_bakery():
    feature = {"properties": {"name": "Utopía", "datasource": {"raw": {"cuisine": "coffee_shop"}}}}
    assert _is_bakery(feature) is False
