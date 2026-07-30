from app.services.ingestion import _build_rows
from app.services.maps_client import GeoapifyPlace


def test_build_rows_filtra_sin_external_id():
    places = [
        GeoapifyPlace(name="A", lat=1.0, lon=2.0, external_id="a", has_wifi=True),
        GeoapifyPlace(name="B", lat=3.0, lon=4.0, external_id=None),
    ]
    rows = _build_rows(places)

    assert len(rows) == 1
    assert rows[0]["external_id"] == "a"
    assert rows[0]["name"] == "A"
    assert rows[0]["has_wifi"] is True
