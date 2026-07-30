import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CoffeeShop as CoffeeShopModel
from app.db.repository import find_nearby
from app.schemas.coffee import CoffeeShop, CoffeeShopCandidate, SearchResult
from app.schemas.intent import IntentProfile
from app.services.ingestion import ingest_area
from app.services.maps_client import fetch_opening_hours, geocode, is_open_now

logger = logging.getLogger(__name__)

_MIN_NEARBY = 6
_WIDEN_LADDER_M = [2000, 3000, 5000, 8000]
_VALIDATE_TOP = 12
_INGEST_RADIUS_M = 2000

_ShopHits = list[tuple[CoffeeShopModel, float]]


async def _base_search(
    session: AsyncSession, lat: float, lon: float, intent: IntentProfile
) -> _ShopHits:
    """Cafeterias dentro del radio base (barrio), ya ordenadas por proximidad."""
    return await find_nearby(session, lat, lon, intent.radius_m, needs_wifi=intent.needs_wifi)


async def _widen_search(
    session: AsyncSession, lat: float, lon: float, intent: IntentProfile
) -> tuple[_ShopHits, int]:
    """Ultimo recurso cuando no hay nada cerca: ensancha y devuelve el PRIMER radio con resultados."""
    for radius in _WIDEN_LADDER_M:
        if radius <= intent.radius_m:
            continue
        found = await find_nearby(session, lat, lon, radius, needs_wifi=intent.needs_wifi)
        if found:
            return found, radius
    return [], intent.radius_m


async def _safe_ingest(session: AsyncSession, lat: float, lon: float) -> None:
    """Siembra la zona pedida en la BD; degradado elegante y con log si Geoapify falla."""
    try:
        count = await ingest_area(session, lat, lon, radius_m=_INGEST_RADIUS_M, limit=50)
        logger.info("Ingesta de zona (%.4f, %.4f): %s cafeterias sembradas", lat, lon, count)
    except Exception:
        logger.warning("Ingesta de zona (%.4f, %.4f) fallo", lat, lon, exc_info=True)


async def search(session: AsyncSession, intent: IntentProfile) -> SearchResult:
    """Agente de busqueda y validacion, proximidad-primero.

    geocode(area) -> (1) busca ceñido al radio base; (2) si hay pocas cerca, siembra la zona
    pedida desde Geoapify (coffee_shop, con respaldo a catering.cafe) y reintenta ceñido;
    (3) solo si sigue sin haber NADA cerca, ensancha por escalones y usa el primer radio con
    resultados. Luego valida "abierto ahora" en vivo. Degradado elegante en cada paso.
    """
    if not intent.area:
        return SearchResult(candidates=[], radius_m=intent.radius_m)

    coords = await geocode(intent.area)
    if coords is None:
        return SearchResult(candidates=[], radius_m=intent.radius_m)
    lat, lon = coords

    nearby = await _base_search(session, lat, lon, intent)
    radius = intent.radius_m

    if len(nearby) < _MIN_NEARBY:
        await _safe_ingest(session, lat, lon)
        nearby = await _base_search(session, lat, lon, intent)

    if not nearby:
        nearby, radius = await _widen_search(session, lat, lon, intent)

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
