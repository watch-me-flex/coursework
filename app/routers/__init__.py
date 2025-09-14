from fastapi import APIRouter
from app.config import settings
from .router import router

api_router = APIRouter()
api_prefix = f"{settings.API_PREFIX}/v{settings.VERSION.split('.')[0]}"

api_router.include_router(
    router,
    prefix=api_prefix,
    tags=["v1"]
)

__all__ = ["api_router", "api_prefix"]
