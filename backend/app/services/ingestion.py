from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CoffeeShop
from app.services.maps_client import GeoapifyPlace, search_cafes

_UPSERT_FIELDS = ("name", "address", "city", "lat", "lon", "opening_hours", "has_wifi")


def _build_rows(places: list[GeoapifyPlace]) -> list[dict]:
    """Convierte los lugares de Geoapify en filas listas para upsert (descarta sin external_id)."""
    return [
        {
            "name": p.name,
            "address": p.address,
            "city": p.city,
            "lat": p.lat,
            "lon": p.lon,
            "external_id": p.external_id,
            "opening_hours": p.opening_hours,
            "has_wifi": p.has_wifi,
        }
        for p in places
        if p.external_id
    ]


async def ingest_area(
    session: AsyncSession, lat: float, lon: float, radius_m: int = 1500, limit: int = 50
) -> int:
    """Trae cafeterias de Geoapify para una zona y las persiste (upsert por external_id).

    Devuelve el numero de cafeterias insertadas/actualizadas.
    """
    places = await search_cafes(lat, lon, radius_m=radius_m, limit=limit)
    rows = _build_rows(places)
    if not rows:
        return 0

    stmt = insert(CoffeeShop).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["external_id"],
        set_={field: stmt.excluded[field] for field in _UPSERT_FIELDS},
    )
    await session.execute(stmt)
    await session.commit()
    return len(rows)
