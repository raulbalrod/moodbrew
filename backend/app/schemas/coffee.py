from pydantic import BaseModel, ConfigDict


class CoffeeShop(BaseModel):
    """Cafeteria tal como se lee de la base de datos local (datos de Geoapify/OSM)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str | None = None
    city: str | None = None
    lat: float
    lon: float
    external_id: str | None = None
    opening_hours: str | None = None
    has_wifi: bool = False


class CoffeeShopCandidate(BaseModel):
    """Candidato que emite el agente de busqueda tras el filtrado y la validacion en vivo."""

    shop: CoffeeShop
    is_open: bool | None = None
    distance_m: float | None = None


class SearchResult(BaseModel):
    """Salida del agente de busqueda: candidatos y el radio realmente usado."""

    candidates: list[CoffeeShopCandidate]
    radius_m: int
