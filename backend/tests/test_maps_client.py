from app.services.maps_client import (
    GeoapifyPlace,
    _extract_attributes,
    _is_bakery,
    _is_commodity_chain,
    _parse_place,
    _specialty_score,
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


def test_parse_place_nombre_numerico():
    place = _parse_place({"properties": {"name": 365, "lat": 1.0, "lon": 2.0, "datasource": {}}})
    assert place.name == "365"


def test_parse_place_marca_coffee_shop_por_categoria():
    feature = {
        "properties": {
            "name": "Blackbird",
            "lat": 1.0,
            "lon": 2.0,
            "categories": ["catering", "catering.cafe", "catering.cafe.coffee_shop"],
            "datasource": {"raw": {}},
        }
    }
    assert _parse_place(feature).is_coffee_shop is True


def test_is_commodity_chain_por_nombre():
    feature = {"properties": {"name": "Starbucks Sol"}}
    assert _is_commodity_chain(feature) is True


def test_is_commodity_chain_por_brand():
    feature = {"properties": {"name": "Cafe X", "datasource": {"raw": {"brand": "Costa Coffee"}}}}
    assert _is_commodity_chain(feature) is True


def test_is_commodity_chain_por_brand_wikidata():
    feature = {"properties": {"name": "Cadena Local", "datasource": {"raw": {"brand:wikidata": "Q42"}}}}
    assert _is_commodity_chain(feature) is True


def test_especialidad_no_es_cadena():
    feature = {"properties": {"name": "Toma Cafe", "datasource": {"raw": {"cuisine": "coffee_shop"}}}}
    assert _is_commodity_chain(feature) is False


def test_is_bakery_por_shop():
    feature = {"properties": {"name": "Santa Gloria", "datasource": {"raw": {"shop": "bakery"}}}}
    assert _is_bakery(feature) is True


def test_is_bakery_por_nombre():
    feature = {"properties": {"name": "Horno Nueva Florida", "datasource": {"raw": {}}}}
    assert _is_bakery(feature) is True


def test_is_bakery_chocolateria_churreria():
    for nombre in ("Chocolatería San Ginés", "Churrería Los Artesanos"):
        feature = {"properties": {"name": nombre, "datasource": {"raw": {"cuisine": "coffee_shop"}}}}
        assert _is_bakery(feature) is True


def test_cafe_no_es_bakery():
    feature = {"properties": {"name": "Utopía", "datasource": {"raw": {"cuisine": "coffee_shop"}}}}
    assert _is_bakery(feature) is False


def test_extract_attributes_selecciona_tags_utiles():
    raw = {
        "cuisine": "coffee_shop",
        "outdoor_seating": "yes",
        "wheelchair": "yes",
        "diet:vegan": "yes",
        "website": "https://dabov.coffee/",
        "contact:instagram": "dabovspecialtycoffee",
        "wikidata": "Q5103675",
        "irrelevante": "x",
    }
    attrs = _extract_attributes({}, raw)
    assert attrs["cuisine"] == "coffee_shop"
    assert attrs["outdoor_seating"] == "yes"
    assert attrs["diet_vegan"] == "yes"
    assert attrs["website"] == "https://dabov.coffee/"
    assert attrs["social"] is True
    assert attrs["notable"] is True
    assert "irrelevante" not in attrs


def test_specialty_score_premia_senales_de_especialidad():
    raw = {
        "cuisine": "coffee_shop",
        "name:en": "Dabov Specialty Coffee",
        "website": "https://dabov.coffee/",
        "contact:instagram": "dabovspecialtycoffee",
        "check_date": "2025-02-14",
    }
    attrs = _extract_attributes({}, raw)
    assert _specialty_score("Dabov", raw, attrs) >= 9


def test_specialty_score_bajo_para_cafe_sin_senales():
    raw = {"amenity": "cafe"}
    assert _specialty_score("Bar Paco", raw, _extract_attributes({}, raw)) == 0


def test_parse_place_incluye_atributos_y_score():
    feature = {
        "properties": {
            "name": "Dabov",
            "lat": 40.4,
            "lon": -3.7,
            "place_id": "d1",
            "datasource": {
                "raw": {
                    "cuisine": "coffee_shop",
                    "name:en": "Dabov Specialty Coffee",
                    "outdoor_seating": "yes",
                    "website": "https://dabov.coffee/",
                    "contact:instagram": "dabov",
                }
            },
        }
    }
    place = _parse_place(feature)
    assert place.specialty_score >= 6
    assert place.attributes["outdoor_seating"] == "yes"
    assert place.attributes["social"] is True
