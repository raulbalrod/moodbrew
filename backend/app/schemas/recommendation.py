from pydantic import BaseModel

from app.schemas.coffee import CoffeeShopCandidate
from app.schemas.intent import IntentProfile


class RecommendationRequest(BaseModel):
    text: str


class Recommendation(BaseModel):
    """Opcion final razonada que produce el agente curador."""

    candidate: CoffeeShopCandidate
    reasoning: str


class RecommendationResponse(BaseModel):
    query: str
    intent: IntentProfile
    recommendations: list[Recommendation]
    search_radius_m: int | None = None
    message: str | None = None
