from fastapi import APIRouter

from app.core.config import settings
from app.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        og_key_configured=bool(settings.og_private_key),
    )
