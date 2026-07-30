from app.services.ingestion import _build_rows, _merge
from app.services.maps_client import GeoapifyPlace


def test_merge_deduplica_por_clave_natural_y_marca_coffee_shop():
    # El MISMO local llega con external_id distinto en cada consulta (comportamiento real de
    # Geoapify): debe quedar UNA fila, marcada coffee_shop.
    broad = [GeoapifyPlace(name="Ozik", lat=37.386394, lon=-5.9961344, external_id="broad-id")]
    coffee = [GeoapifyPlace(name="Ozik", lat=37.386394, lon=-5.9961344, external_id="coffee-id")]

    merged = _merge(broad, coffee)

    assert len(merged) == 1
    assert merged[0].is_coffee_shop is True
    assert merged[0].external_id == "broad-id"  # la amplia es la canonica


def test_build_rows_filtra_sin_external_id():
    places = [
        GeoapifyPlace(
            name="A",
            lat=1.0,
            lon=2.0,
            external_id="a",
            has_wifi=True,
            attributes={"outdoor_seating": "yes"},
            specialty_score=5,
        ),
        GeoapifyPlace(name="B", lat=3.0, lon=4.0, external_id=None),
    ]
    rows = _build_rows(places)

    assert len(rows) == 1
    assert rows[0]["external_id"] == "a"
    assert rows[0]["name"] == "A"
    assert rows[0]["has_wifi"] is True
    assert rows[0]["attributes"] == {"outdoor_seating": "yes"}
    assert rows[0]["specialty_score"] == 5
