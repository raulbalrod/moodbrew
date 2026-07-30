from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CoffeeShop as CoffeeShopModel
from app.db.repository import find_nearby
from app.schemas.coffee import CoffeeShop, CoffeeShopCandidate, SearchResult
from app.schemas.intent import IntentProfile
from app.services.ingestion import ingest_area
from app.services.maps_client import fetch_opening_hours, geocode, is_open_now

_RADIUS_STEPS_M = [0, 1000, 4000]
_MAX_RADIUS_M = 8000
_MIN_CANDIDATES = 5
_VALIDATE_TOP = 8
_INGEST_RADIUS_M = 5000


async def _progressive_search(
    session: AsyncSession, lat: float, lon: float, intent: IntentProfile
) -> tuple[list[tuple[CoffeeShopModel, float]], int]:
    """Busca en Postgres ampliando el radio; devuelve (candidatos, radio_usado)."""
    nearby: list[tuple[CoffeeShopModel, float]] = []
    radius = intent.radius_m
    best_count = -1
    for step in _RADIUS_STEPS_M:
        current_radius = min(intent.radius_m + step, _MAX_RADIUS_M)
        found = await find_nearby(session, lat, lon, current_radius, needs_wifi=intent.needs_wifi)
        if len(found) > best_count:
            nearby, radius, best_count = found, current_radius, len(found)
            if best_count >= _MIN_CANDIDATES:
                break
    return nearby, radius


async def _db_search(
    session: AsyncSession, lat: float, lon: float, intent: IntentProfile
) -> tuple[list[tuple[CoffeeShopModel, float]], int]:
    """Busca en la BD: ceñido al radio base y, si hay pocos, con ensanche progresivo."""
    nearby = await find_nearby(session, lat, lon, intent.radius_m, needs_wifi=intent.needs_wifi)
    radius = intent.radius_m
    if len(nearby) < _MIN_CANDIDATES:
        nearby, radius = await _progressive_search(session, lat, lon, intent)
    return nearby, radius


async def _safe_ingest(session: AsyncSession, lat: float, lon: float) -> None:
    """Ingesta una zona ancha; degradado elegante si Geoapify falla."""
    try:
        await ingest_area(session, lat, lon, radius_m=_INGEST_RADIUS_M, limit=50)
    except Exception:
        pass


async def search(session: AsyncSession, intent: IntentProfile) -> SearchResult:
    """Agente de busqueda y validacion.

    geocode(area) -> filtrado ceñido en Postgres. Si la zona no esta cacheada, la trae
    de Geoapify (coffee_shop) y reintenta; como ultimo recurso, en zonas mal etiquetadas,
    amplia a `catering.cafe`. Luego valida "abierto ahora" en vivo. Degradado elegante.
    """
    if not intent.area:
        return SearchResult(candidates=[], radius_m=intent.radius_m)

    coords = await geocode(intent.area)
    if coords is None:
        return SearchResult(candidates=[], radius_m=intent.radius_m)
    lat, lon = coords

    nearby, radius = await _db_search(session, lat, lon, intent)

    if len(nearby) < _MIN_CANDIDATES:
        await _safe_ingest(session, lat, lon)
        nearby, radius = await _db_search(session, lat, lon, intent)

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
