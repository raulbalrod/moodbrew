from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CoffeeShop
from app.services.maps_client import GeoapifyPlace, search_cafes

_CAFE_CATEGORY = "catering.cafe"
_COFFEE_SHOP_CATEGORY = "catering.cafe.coffee_shop"

_UPSERT_FIELDS = (
    "name",
    "address",
    "city",
    "lat",
    "lon",
    "opening_hours",
    "has_wifi",
    "is_coffee_shop",
    "attributes",
    "specialty_score",
)


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
            "is_coffee_shop": p.is_coffee_shop,
            "attributes": p.attributes,
            "specialty_score": p.specialty_score,
        }
        for p in places
        if p.external_id
    ]


def _dedup_key(place: GeoapifyPlace) -> tuple:
    """Clave natural de un local: Geoapify da distinto external_id por consulta para el MISMO
    sitio, asi que deduplicamos por nombre + coordenadas (no por id)."""
    return (place.name.strip().lower(), round(place.lat, 5), round(place.lon, 5))


def _merge(broad: list[GeoapifyPlace], coffee: list[GeoapifyPlace]) -> list[GeoapifyPlace]:
    """Une ambas consultas por clave natural; lo que aparece en la estrecha se marca coffee_shop."""
    coffee_keys = {_dedup_key(p) for p in coffee if p.external_id}
    merged: dict[tuple, GeoapifyPlace] = {}
    for place in broad + coffee:  # la amplia va primero: conserva su external_id como canonico
        if not place.external_id:
            continue
        key = _dedup_key(place)
        if key in coffee_keys:
            place.is_coffee_shop = True
        if key in merged:
            merged[key].is_coffee_shop = merged[key].is_coffee_shop or place.is_coffee_shop
        else:
            merged[key] = place
    return list(merged.values())


async def ingest_area(
    session: AsyncSession, lat: float, lon: float, radius_m: int = 1500, limit: int = 50
) -> int:
    """Trae cafeterias de Geoapify para una zona y las persiste (upsert por external_id).

    Consulta la categoria amplia (`catering.cafe`, cobertura) y la estrecha
    (`catering.cafe.coffee_shop`, especialidad fiable) al MISMO radio, y las fusiona.
    Devuelve el numero de cafeterias insertadas/actualizadas.
    """
    broad = await search_cafes(
        lat, lon, radius_m=radius_m, limit=limit, categories=_CAFE_CATEGORY
    )
    try:
        coffee = await search_cafes(
            lat, lon, radius_m=radius_m, limit=limit, categories=_COFFEE_SHOP_CATEGORY
        )
    except Exception:
        coffee = []
    rows = _build_rows(_merge(broad, coffee))
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
