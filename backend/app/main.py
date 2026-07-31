from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(api_router, prefix="/api")
