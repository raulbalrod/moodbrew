from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.pipeline import run_pipeline
from app.rate_limit import limiter
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse

router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse)
@limiter.limit(lambda: settings.rate_limit)
async def recommendations(
    request: Request,
    payload: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Recibe texto libre y devuelve 2-3 cafeterias de especialidad razonadas."""
    return await run_pipeline(db, payload.text)
