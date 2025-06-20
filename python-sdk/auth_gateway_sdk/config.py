"""
Configuration management for Auth Gateway SDK.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class AuthGatewayConfig(BaseModel):
    """Configuration for Auth Gateway SDK."""
    
    base_url: str = Field(..., description="Auth Gateway base URL")
    timeout: int = Field(30, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts for failed requests")
    verify_ssl: bool = Field(True, description="Whether to verify SSL certificates")
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate and normalize base URL."""
        if not v:
            raise ValueError("base_url cannot be empty")
        
        # Remove trailing slash for consistency
        return v.rstrip('/')
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout value."""
        if v <= 0:
            raise ValueError("timeout must be greater than 0")
        return v
    
    @field_validator('retry_attempts')
    @classmethod
    def validate_retry_attempts(cls, v: int) -> int:
        """Validate retry attempts."""
        if v < 0:
            raise ValueError("retry_attempts cannot be negative")
        return v
    
    @classmethod
    def from_env(cls, prefix: str = "AUTH_GATEWAY_") -> "AuthGatewayConfig":
        """Create configuration from environment variables."""
        base_url = os.getenv(f"{prefix}URL")
        if not base_url:
            raise ValueError(
                f"Environment variable {prefix}URL is required. "
                "Set it to your Auth Gateway URL (e.g., https://auth.example.com)"
            )
        
        return cls(
            base_url=base_url,
            timeout=int(os.getenv(f"{prefix}TIMEOUT", "30")),
            retry_attempts=int(os.getenv(f"{prefix}RETRY_ATTEMPTS", "3")),
            verify_ssl=os.getenv(f"{prefix}VERIFY_SSL", "true").lower() == "true",
        )
    
    @classmethod
    def from_url(cls, base_url: str, **kwargs) -> "AuthGatewayConfig":
        """Create configuration with just a base URL and optional overrides."""
        return cls(base_url=base_url, **kwargs)


def get_default_config() -> Optional[AuthGatewayConfig]:
    """Get default configuration from environment variables if available."""
    try:
        return AuthGatewayConfig.from_env()
    except ValueError:
        return None
