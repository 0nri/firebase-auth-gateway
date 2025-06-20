"""
Custom exceptions for Auth Gateway SDK.
"""


class AuthGatewayException(Exception):
    """Base exception for all Auth Gateway SDK errors."""
    
    def __init__(self, message: str, status_code: int = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(AuthGatewayException):
    """Raised when authentication fails."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""
    pass


class TokenInvalidError(AuthenticationError):
    """Raised when a token is invalid or malformed."""
    pass


class DomainNotAllowedError(AuthenticationError):
    """Raised when user's email domain is not allowed."""
    pass


class NetworkError(AuthGatewayException):
    """Raised when network/HTTP requests fail."""
    pass


class ConfigurationError(AuthGatewayException):
    """Raised when SDK is misconfigured."""
    pass


class RateLimitError(AuthGatewayException):
    """Raised when API rate limits are exceeded."""
    pass
