from fastapi import APIRouter

from .analysis import router as analysis_router
from .health import router as health_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(analysis_router)

__all__ = ["api_router"]
