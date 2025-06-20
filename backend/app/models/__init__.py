"""Models package for Auth Gateway."""

from .requests import (
    AuthCallbackRequest,
    LoginRequest
)
from .responses import (
    UserData,
    AuthCallbackResponse,
    LoginResponse,
    ErrorResponse,
    HealthResponse
)

__all__ = [
    "AuthCallbackRequest",
    "LoginRequest",
    "UserData",
    "AuthCallbackResponse",
    "LoginResponse",
    "ErrorResponse",
    "HealthResponse"
]
