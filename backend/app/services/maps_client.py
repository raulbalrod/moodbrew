import httpx
from pydantic import BaseModel

from app.config import settings

GEOAPIFY_BASE_URL = "https://api.geoapify.com"
_WIFI_VALUES = {"wlan", "yes", "wifi", "free", "wlan;yes"}


class GeoapifyPlace(BaseModel):
    """Cafeteria extraida de Geoapify/OSM (sin persistir todavia)."""

    name: str
    address: str | None = None
    city: str | None = None
    lat: float
    lon: float
    external_id: str | None = None
    opening_hours: str | None = None
    has_wifi: bool = False


async def geocode(text: str) -> tuple[float, float] | None:
    """Convierte una zona/direccion en coordenadas (lat, lon) via Geoapify Geocoding."""
    params = {"text": text, "limit": 1, "apiKey": settings.geoapify_api_key}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{GEOAPIFY_BASE_URL}/v1/geocode/search", params=params)
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        return None
    props = features[0]["properties"]
    return props["lat"], props["lon"]


async def search_cafes(
    lat: float, lon: float, radius_m: int = 1500, limit: int = 20
) -> list[GeoapifyPlace]:
    """Busca cafeterias alrededor de (lat, lon) via Geoapify Places API."""
    params = {
        "categories": "catering.cafe",
        "filter": f"circle:{lon},{lat},{radius_m}",
        "bias": f"proximity:{lon},{lat}",
        "limit": limit,
        "apiKey": settings.geoapify_api_key,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{GEOAPIFY_BASE_URL}/v2/places", params=params)
    response.raise_for_status()
    return [_parse_place(feature) for feature in response.json().get("features", [])]


def _parse_place(feature: dict) -> GeoapifyPlace:
    props = feature["properties"]
    raw = (props.get("datasource") or {}).get("raw") or {}
    return GeoapifyPlace(
        name=props.get("name") or "Cafeteria sin nombre",
        address=props.get("formatted"),
        city=props.get("city"),
        lat=props["lat"],
        lon=props["lon"],
        external_id=props.get("place_id"),
        opening_hours=raw.get("opening_hours"),
        has_wifi=str(raw.get("internet_access", "")).lower() in _WIFI_VALUES,
    )
