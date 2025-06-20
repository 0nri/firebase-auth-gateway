"""
Health check endpoints for Auth Gateway.
"""
from fastapi import APIRouter
from ..models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        service="Auth Gateway",
        version="1.0.0"
    )


@router.get("/health", response_model=HealthResponse)
async def health_check_explicit():
    """Explicit health check endpoint."""
    return HealthResponse(
        status="ok",
        service="Auth Gateway",
        version="1.0.0"
    )
