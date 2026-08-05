from pydantic import BaseModel, Field

from app.schemas.coffee import CoffeeShopCandidate
from app.schemas.intent import IntentProfile


class RecommendationRequest(BaseModel):
    text: str


class Recommendation(BaseModel):
    """Opcion final razonada que produce el agente curador."""

    candidate: CoffeeShopCandidate
    reasoning: str


class CurationResult(BaseModel):
    """Salida del curador: destacadas y secundarias, razonadas en una sola llamada."""

    curated: list[Recommendation]
    nearby: list[Recommendation]


class RecommendationResponse(BaseModel):
    query: str
    intent: IntentProfile
    recommendations: list[Recommendation]
    nearby: list[Recommendation] = Field(default_factory=list)
    search_radius_m: int | None = None
    message: str | None = None
