from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.curator_agent import curate
from app.agents.intent_agent import parse_intent
from app.agents.search_agent import search
from app.schemas.recommendation import RecommendationResponse

_NOT_FOUND_MESSAGE = (
    "No he encontrado cafeterías de especialidad cerca de esa ubicación. "
    "Prueba con un sitio más concreto —una calle, plaza o barrio— para afinar la búsqueda."
)


async def run_pipeline(session: AsyncSession, text: str) -> RecommendationResponse:
    """Orquesta la tuberia secuencial: intencion -> busqueda -> curacion."""
    intent = await parse_intent(text)
    search_result = await search(session, intent)

    if not search_result.candidates:
        return RecommendationResponse(
            query=text, intent=intent, recommendations=[], message=_NOT_FOUND_MESSAGE
        )

    curation = await curate(text, search_result.candidates)
    return RecommendationResponse(
        query=text,
        intent=intent,
        recommendations=curation.curated,
        nearby=curation.nearby,
        search_radius_m=search_result.radius_m,
    )
