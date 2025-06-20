"""
Auth Gateway SDK for Python.

A Python SDK for integrating with the Auth Gateway service, providing
Firebase authentication with Google Sign-In.
"""

__version__ = "1.0.0"

# Core client classes
from .client import AuthGatewayClient, SyncAuthGatewayClient

# Configuration
from .config import AuthGatewayConfig

# Models
from .models import (
    UserData,
    LoginRequest,
    LoginResponse,
    AuthCallbackRequest,
    AuthCallbackResponse,
    HealthResponse,
    ErrorResponse,
    LogoutResponse,
)

# Exceptions
from .exceptions import (
    AuthGatewayException,
    AuthenticationError,
    TokenExpiredError,
    TokenInvalidError,
    DomainNotAllowedError,
    NetworkError,
    ConfigurationError,
    RateLimitError,
)

# Main public API
__all__ = [
    # Version
    "__version__",
    
    # Core clients
    "AuthGatewayClient",
    "SyncAuthGatewayClient",
    
    # Configuration
    "AuthGatewayConfig",
    
    # Models
    "UserData",
    "LoginRequest", 
    "LoginResponse",
    "AuthCallbackRequest",
    "AuthCallbackResponse",
    "HealthResponse",
    "ErrorResponse",
    "LogoutResponse",
    
    # Exceptions
    "AuthGatewayException",
    "AuthenticationError",
    "TokenExpiredError",
    "TokenInvalidError",
    "DomainNotAllowedError",
    "NetworkError",
    "ConfigurationError",
    "RateLimitError",
]
