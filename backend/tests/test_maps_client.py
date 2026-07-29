from app.services.maps_client import GeoapifyPlace, _parse_place


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
