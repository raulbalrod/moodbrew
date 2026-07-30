"""Seed de la base de datos: puebla `coffee_shops` desde Geoapify (sin datos manuales).

Uso:
    python -m scripts.seed_database --area "Madrid, Spain" --radius 1500 --limit 50
"""

import argparse
import asyncio

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.ingestion import ingest_area
from app.services.maps_client import geocode


async def seed(area: str, radius_m: int, limit: int) -> int:
    """Geocodifica la zona y persiste sus cafeterias (upsert por `external_id`)."""
    coords = await geocode(area)
    if coords is None:
        raise SystemExit(f"No se pudo geocodificar la zona: {area!r}")
    lat, lon = coords

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        return await ingest_area(session, lat, lon, radius_m=radius_m, limit=limit)


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
