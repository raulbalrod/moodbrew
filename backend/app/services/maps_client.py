import re
from datetime import datetime

import httpx
from pydantic import BaseModel, Field

from app.config import settings

GEOAPIFY_BASE_URL = "https://api.geoapify.com"
_WIFI_VALUES = {"wlan", "yes", "wifi", "free", "wlan;yes"}
_CAFE_CATEGORIES = "catering.cafe.coffee_shop"
_SPECIALTY_NAME_HINTS = (
    "specialty",
    "speciality",
    "especialidad",
    "roaster",
    "roasters",
    "tostador",
    "tostadero",
    "third wave",
    "micro roaster",
)
_ATTRIBUTE_TAGS = {
    "cuisine": "cuisine",
    "outdoor_seating": "outdoor_seating",
    "indoor_seating": "indoor_seating",
    "wheelchair": "wheelchair",
    "takeaway": "takeaway",
    "air_conditioning": "air_conditioning",
    "diet:vegan": "diet_vegan",
    "diet:vegetarian": "diet_vegetarian",
}
_CHAIN_DENYLIST = {
    "starbucks",
    "costa coffee",
    "caffe nero",
    "caffè nero",
    "mccafe",
    "mccafé",
    "dunkin",
    "nespresso",
    "segafredo",
    "tim hortons",
}
_BAKERY_NAME_HINTS = (
    "horno",
    "panaderia",
    "panadería",
    "pasteleria",
    "pastelería",
    "confiteria",
    "confitería",
    "obrador",
    "chocolateria",
    "chocolatería",
    "churreria",
    "churrería",
    "churros",
)


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
    is_coffee_shop: bool = False
    attributes: dict = Field(default_factory=dict)
    specialty_score: int = 0


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
    lat: float,
    lon: float,
    radius_m: int = 1500,
    limit: int = 20,
    categories: str = _CAFE_CATEGORIES,
) -> list[GeoapifyPlace]:
    """Busca cafeterias de especialidad alrededor de (lat, lon) via Geoapify Places API.

    `categories` permite ampliar de `catering.cafe.coffee_shop` (estrecho) a `catering.cafe`
    (generico) en zonas mal etiquetadas en OSM. Los filtros de cadena y panaderia siguen
    aplicandose, asi que ampliar no cuela franquicias ni obradores.
    """
    params = {
        "categories": categories,
        "filter": f"circle:{lon},{lat},{radius_m}",
        "bias": f"proximity:{lon},{lat}",
        "limit": limit,
        "apiKey": settings.geoapify_api_key,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{GEOAPIFY_BASE_URL}/v2/places", params=params)
    response.raise_for_status()
    return [
        _parse_place(feature)
        for feature in response.json().get("features", [])
        if _has_name(feature)
        and not _is_commodity_chain(feature)
        and not _is_bakery(feature)
    ]


def _has_name(feature: dict) -> bool:
    """Descarta locales sin nombre en OSM: no tiene sentido recomendar 'Cafeteria sin nombre'."""
    return bool(str((feature.get("properties") or {}).get("name") or "").strip())


def _is_coffee_shop(props: dict, raw: dict) -> bool:
    """Señal fuerte de especialidad: OSM clasifica el local como coffee_shop.

    Combina la categoria de Geoapify con los tags OSM (`cuisine`, `shop=coffee`) porque
    ninguna fuente sola es completa en la consulta amplia.
    """
    if "catering.cafe.coffee_shop" in (props.get("categories") or []):
        return True
    if "coffee_shop" in str(raw.get("cuisine", "")).lower():
        return True
    return str(raw.get("shop", "")).lower() == "coffee"


def _is_bakery(feature: dict) -> bool:
    """Detecta panaderias/pastelerias/chocolaterias/churrerias.

    Sirven cafe pero no son cafeterias de cafe de especialidad, asi que se excluyen.
    """
    props = feature.get("properties", {})
    raw = (props.get("datasource") or {}).get("raw") or {}
    if str(raw.get("shop", "")).lower() == "bakery":
        return True
    name = str(props.get("name") or "").lower()
    return any(hint in name for hint in _BAKERY_NAME_HINTS)


def _is_commodity_chain(feature: dict) -> bool:
    """Detecta cadenas comerciales (no especialidad).

    En OSM las franquicias se marcan con `brand`/`brand:wikidata`; su sola presencia
    delata una cadena en cualquier idioma. El denylist queda como red de seguridad.
    """
    props = feature.get("properties", {})
    raw = (props.get("datasource") or {}).get("raw") or {}
    if raw.get("brand:wikidata") or raw.get("brand"):
        return True
    text = " ".join(
        str(value) for value in (props.get("name"), raw.get("operator")) if value
    ).lower()
    return any(chain in text for chain in _CHAIN_DENYLIST)


def _extract_attributes(props: dict, raw: dict) -> dict:
    """Selecciona los tags OSM objetivos utiles para rankear y explicar el local."""
    attrs: dict = {}
    for tag, key in _ATTRIBUTE_TAGS.items():
        value = raw.get(tag)
        if value is not None:
            attrs[key] = value
    website = raw.get("website") or props.get("website")
    if website:
        attrs["website"] = website
    if raw.get("contact:instagram") or raw.get("contact:facebook"):
        attrs["social"] = True
    if raw.get("wikidata") or raw.get("wikipedia"):
        attrs["notable"] = True
    return attrs


def _specialty_score(name: str, raw: dict, attrs: dict) -> int:
    """Puntuacion heuristica de 'especialidad' a partir de senales OSM (determinista)."""
    score = 0
    if "coffee_shop" in str(raw.get("cuisine", "")).lower():
        score += 2
    text = f"{name} {raw.get('name:en', '')}".lower()
    if any(hint in text for hint in _SPECIALTY_NAME_HINTS):
        score += 3
    if attrs.get("website"):
        score += 1
    if attrs.get("social"):
        score += 2
    if attrs.get("notable"):
        score += 1
    if raw.get("check_date"): 
        score += 1
    if len(raw) >= 12:
        score += 1
    return score


def _parse_place(feature: dict) -> GeoapifyPlace:
    props = feature["properties"]
    raw = (props.get("datasource") or {}).get("raw") or {}
    name = str(props.get("name") or "Cafeteria sin nombre")
    attrs = _extract_attributes(props, raw)
    return GeoapifyPlace(
        name=name,
        address=props.get("formatted"),
        city=props.get("city"),
        lat=props["lat"],
        lon=props["lon"],
        external_id=props.get("place_id"),
        opening_hours=raw.get("opening_hours"),
        has_wifi=str(raw.get("internet_access", "")).lower() in _WIFI_VALUES,
        is_coffee_shop=_is_coffee_shop(props, raw),
        attributes=attrs,
        specialty_score=_specialty_score(name, raw, attrs),
    )


async def fetch_opening_hours(external_id: str) -> str | None:
    """Consulta Place Details de Geoapify y devuelve el `opening_hours` (OSM) si existe.

    Degradado elegante: ante cualquier fallo de red/API devuelve None (horario desconocido).
    """
    params = {"id": external_id, "features": "details", "apiKey": settings.geoapify_api_key}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{GEOAPIFY_BASE_URL}/v2/place-details", params=params)
        response.raise_for_status()
    except Exception:
        return None
    for feature in response.json().get("features", []):
        props = feature.get("properties", {})
        raw = (props.get("datasource") or {}).get("raw") or {}
        opening_hours = props.get("opening_hours") or raw.get("opening_hours")
        if opening_hours:
            return opening_hours
    return None


_WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
_TIME_RANGE = re.compile(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})")
_DAY_TOKEN = re.compile(r"^(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?$")


def _expand_days(day_spec: str) -> set[str] | None:
    days: set[str] = set()
    for token in day_spec.split(","):
        token = token.strip()
        if not token:
            continue
        match = _DAY_TOKEN.match(token)
        if not match:
            return None
        start = _WEEKDAYS.index(match.group(1))
        end = _WEEKDAYS.index(match.group(2)) if match.group(2) else start
        if end >= start:
            days.update(_WEEKDAYS[start : end + 1])
        else:  # rango que envuelve la semana, p.ej. Sa-Mo
            days.update(_WEEKDAYS[start:] + _WEEKDAYS[: end + 1])
    return days


def _eval_rule(rule: str, weekday: str, minutes_now: int) -> bool | None:
    ranges = _TIME_RANGE.findall(rule)
    day_part = _TIME_RANGE.sub("", rule)
    closed = bool(re.search(r"\b(off|closed)\b", day_part, flags=re.I))
    day_part = re.sub(r"\b(off|closed)\b", "", day_part, flags=re.I).strip()

    if day_part:
        days = _expand_days(day_part)
        if days is None:
            return None
        if weekday not in days:
            return None  # la regla no aplica hoy
    if closed:
        return False
    if not ranges:
        return None
    for h1, m1, h2, m2 in ranges:
        start = int(h1) * 60 + int(m1)
        end = int(h2) * 60 + int(m2)
        if end <= start:  # cruza medianoche
            if minutes_now >= start or minutes_now < end:
                return True
        elif start <= minutes_now < end:
            return True
    return False


def is_open_now(opening_hours: str | None, now: datetime | None = None) -> bool | None:
    """Evalua un `opening_hours` OSM (subconjunto comun) contra `now`.

    Devuelve True/False si puede evaluarlo, o None si falta el dato o no lo entiende.
    """
    if not opening_hours:
        return None
    text = opening_hours.strip()
    if text == "24/7":
        return True

    now = now or datetime.now()
    weekday = _WEEKDAYS[now.weekday()]
    minutes_now = now.hour * 60 + now.minute

    parsed_any = False
    for rule in text.split(";"):
        result = _eval_rule(rule.strip(), weekday, minutes_now)
        if result is None:
            continue
        parsed_any = True
        if result:
            return True
    return False if parsed_any else None

