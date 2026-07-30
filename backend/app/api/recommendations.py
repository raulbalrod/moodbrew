from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.pipeline import run_pipeline
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse

router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse)
async def recommendations(
    payload: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Recibe texto libre y devuelve 2-3 cafeterias de especialidad razonadas."""
    return await run_pipeline(db, payload.text)
