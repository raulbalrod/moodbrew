import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CoffeeShop

_EARTH_RADIUS_M = 6_371_000
_METERS_PER_DEGREE = 111_320


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos coordenadas (formula del haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


async def find_nearby(
    session: AsyncSession,
    lat: float,
    lon: float,
    radius_m: int,
    needs_wifi: bool = False,
    limit: int = 20,
) -> list[tuple[CoffeeShop, float]]:
    """Filtra cafeterias en Postgres por bounding-box (+ wifi) y las ordena por distancia.

    Devuelve pares (cafeteria, distancia_en_metros) dentro del radio, mas cercanas primero.
    """
    lat_delta = radius_m / _METERS_PER_DEGREE
    lon_delta = radius_m / (_METERS_PER_DEGREE * math.cos(math.radians(lat)) or 1)

    stmt = select(CoffeeShop).where(
        CoffeeShop.lat.between(lat - lat_delta, lat + lat_delta),
        CoffeeShop.lon.between(lon - lon_delta, lon + lon_delta),
    )
    if needs_wifi:
        stmt = stmt.where(CoffeeShop.has_wifi.is_(True))

    shops = list(await session.scalars(stmt))

    within = [
        (shop, _haversine_m(lat, lon, shop.lat, shop.lon))
        for shop in shops
    ]
    within = [(shop, dist) for shop, dist in within if dist <= radius_m]
    within.sort(key=lambda pair: pair[1])
    return within[:limit]
