"""Seed de la base de datos: puebla `coffee_shops` desde Geoapify (sin datos manuales).

Uso:
    python -m scripts.seed_database --area "Madrid, Spain" --radius 1500 --limit 50
"""

import argparse
import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.db.base import Base
from app.db.models import CoffeeShop
from app.db.session import SessionLocal, engine
from app.services.maps_client import geocode, search_cafes


async def seed(area: str, radius_m: int, limit: int) -> int:
    """Geocodifica la zona, busca cafeterias y hace upsert por `external_id`."""
    coords = await geocode(area)
    if coords is None:
        raise SystemExit(f"No se pudo geocodificar la zona: {area!r}")
    lat, lon = coords

    places = await search_cafes(lat, lon, radius_m=radius_m, limit=limit)
    rows = [
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
        if p.external_id  # necesario para el upsert idempotente
    ]
    if not rows:
        return 0

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    stmt = insert(CoffeeShop).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["external_id"],
        set_={
            "name": stmt.excluded.name,
            "address": stmt.excluded.address,
            "city": stmt.excluded.city,
            "lat": stmt.excluded.lat,
            "lon": stmt.excluded.lon,
            "opening_hours": stmt.excluded.opening_hours,
            "has_wifi": stmt.excluded.has_wifi,
        },
    )
    async with SessionLocal() as session:
        await session.execute(stmt)
        await session.commit()
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Puebla coffee_shops desde Geoapify.")
    parser.add_argument("--area", default="Madrid, Spain", help="Zona a geocodificar.")
    parser.add_argument("--radius", type=int, default=1500, help="Radio de busqueda en metros.")
    parser.add_argument("--limit", type=int, default=50, help="Maximo de cafeterias a traer.")
    args = parser.parse_args()

    count = asyncio.run(seed(args.area, args.radius, args.limit))
    print(f"Insertadas/actualizadas {count} cafeterias en '{args.area}'.")


if __name__ == "__main__":
    main()
