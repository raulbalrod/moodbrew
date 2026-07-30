from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import find_nearby
from app.schemas.coffee import CoffeeShop, CoffeeShopCandidate, SearchResult
from app.schemas.intent import IntentProfile
from app.services.maps_client import fetch_opening_hours, geocode, is_open_now

_RADIUS_STEPS_M = [0, 1000, 4000]
_MAX_RADIUS_M = 8000
_MIN_CANDIDATES = 3
_VALIDATE_TOP = 5

async def search(session: AsyncSession, intent: IntentProfile) -> SearchResult:
    """Agente de busqueda y validacion.

    geocode(area) -> filtrado en Postgres con radio progresivo -> validacion
    "abierto ahora" en vivo de los mejores candidatos. Degradado elegante si
    falta `area` o falla el geocoder.
    """
    if not intent.area:
        return SearchResult(candidates=[], radius_m=intent.radius_m)

    coords = await geocode(intent.area)
    if coords is None:
        return SearchResult(candidates=[], radius_m=intent.radius_m)
    lat, lon = coords

    nearby: list = []
    radius = intent.radius_m
    best_count = -1
    for step in _RADIUS_STEPS_M:
        current_radius = min(intent.radius_m + step, _MAX_RADIUS_M)
        found = await find_nearby(session, lat, lon, current_radius, needs_wifi=intent.needs_wifi)
        if len(found) > best_count:
            nearby, radius, best_count = found, current_radius, len(found)
            if best_count >= _MIN_CANDIDATES:
                break

    candidates: list[CoffeeShopCandidate] = []
    for shop, distance in nearby[:_VALIDATE_TOP]:
        is_open = None
        if shop.external_id:
            opening_hours = shop.opening_hours or await fetch_opening_hours(shop.external_id)
            is_open = is_open_now(opening_hours)
        candidates.append(
            CoffeeShopCandidate(
                shop=CoffeeShop.model_validate(shop),
                is_open=is_open,
                distance_m=round(distance, 1),
            )
        )

    if intent.open_now:
        candidates = [c for c in candidates if c.is_open is not False]

    return SearchResult(candidates=candidates, radius_m=radius)
