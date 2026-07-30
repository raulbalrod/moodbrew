import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CoffeeShop

_EARTH_RADIUS_M = 6_371_000
_METERS_PER_DEGREE = 111_320
_DISTANCE_BUCKET_M = 300


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

    shops = list(await session.scalars(stmt))

    within = [
        (shop, _haversine_m(lat, lon, shop.lat, shop.lon))
        for shop in shops
    ]
    within = [(shop, dist) for shop, dist in within if dist <= radius_m]
    within.sort(key=lambda pair: _rank_key(pair[0], pair[1], needs_wifi))
    return within[:limit]


def _rank_key(shop: CoffeeShop, distance_m: float, prefer_wifi: bool) -> tuple:
    """Clave de orden especialidad-primero, dentro del radio ya acotado por el buscador.

    La categoria con mas peso es coffee_shop: dentro del radio pedido, los coffee_shop van
    arriba (ordenados por cercania entre ellos) y luego los cafes genericos (idem). Dentro de
    cada grupo, a igual banda de distancia (~300 m): si el usuario pidio wifi, las que lo
    tienen suben; luego la mayor especialidad; y a igualdad, la distancia exacta. La cercania
    ordena, pero no sacrifica un coffee_shop del barrio por un bar generico pegado al punto.
    """
    coffee_rank = 0 if shop.is_coffee_shop else 1
    bucket = int(distance_m // _DISTANCE_BUCKET_M)
    wifi_rank = 0 if (prefer_wifi and shop.has_wifi) else 1
    return (coffee_rank, bucket, wifi_rank, -shop.specialty_score, distance_m)
