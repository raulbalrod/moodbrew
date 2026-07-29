from pydantic import BaseModel

from app.schemas.coffee import CoffeeShopCandidate
from app.schemas.intent import IntentProfile


class RecommendationRequest(BaseModel):
    text: str


class Recommendation(BaseModel):
    """Opcion final razonada que produce el Agente 3."""

    candidate: CoffeeShopCandidate
    reasoning: str


class RecommendationResponse(BaseModel):
    query: str
    intent: IntentProfile
    recommendations: list[Recommendation]
