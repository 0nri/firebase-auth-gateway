"""Routes package for Auth Gateway API endpoints."""

from .auth import router as auth_router
from .health import router as health_router

__all__ = ["auth_router", "health_router"]
