"""
Configuration settings and environment variable validation for Auth Gateway.
"""
import os
import re
import logging
from typing import Optional, List
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Firebase Configuration
    firebase_api_key: str
    firebase_auth_domain: str
    firebase_project_id: str
    firebase_app_id: Optional[str] = None
    
    # Google OAuth Configuration
    google_client_id: str
    google_client_secret: str
    
    # Auth Gateway Configuration
    gateway_public_url: str
    auth_redirect_url: Optional[str] = None
    allowed_email_domain_regex: str = ".*"
    
    # CORS Configuration
    cors_allowed_origins: str = ""
    
    # Application Configuration
    log_level: str = "INFO"
    environment: str = "development"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra environment variables
    }
    
    @field_validator('cors_allowed_origins')
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate and parse CORS origins."""
        if not v:
            return []
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    
    @field_validator('allowed_email_domain_regex')
    @classmethod
    def validate_email_regex(cls, v):
        """Validate email domain regex pattern."""
        try:
            re.compile(v)
            return v
        except re.error as e:
            logger.warning(f"Invalid email domain regex '{v}': {e}. Using default '.*'")
            return ".*"
    
    @field_validator('firebase_api_key', 'firebase_auth_domain', 'firebase_project_id')
    @classmethod
    def validate_firebase_config(cls, v, info):
        """Validate required Firebase configuration."""
        if not v:
            raise ValueError(f"{info.field_name} is required for Firebase integration")
        return v
    
    @field_validator('google_client_id', 'google_client_secret')
    @classmethod
    def validate_google_config(cls, v, info):
        """Validate required Google OAuth configuration."""
        if not v:
            raise ValueError(f"{info.field_name} is required for Google OAuth integration")
        return v
    
    @field_validator('gateway_public_url')
    @classmethod
    def validate_gateway_url(cls, v):
        """Validate gateway public URL."""
        if not v:
            raise ValueError("GATEWAY_PUBLIC_URL is required")
        if not v.startswith(('http://', 'https://')):
            raise ValueError("GATEWAY_PUBLIC_URL must start with http:// or https://")
        return v.rstrip('/')
    
    def get_cors_origins(self) -> List[str]:
        """Get parsed CORS origins."""
        return self.cors_allowed_origins


def get_settings() -> Settings:
    """Get application settings with caching."""
    return Settings()


def setup_logging(settings: Settings) -> None:
    """Setup application logging configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger("auth-gateway").setLevel(getattr(logging, settings.log_level.upper()))
    
    # Reduce noise from external libraries in production
    if settings.environment == "production":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
