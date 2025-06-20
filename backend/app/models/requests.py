"""
Request models for Auth Gateway API endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class LoginRequest(BaseModel):
    """Request model for login endpoint."""
    
    redirect_uri: Optional[str] = Field(
        None,
        description="Client application redirect URI after successful authentication"
    )
    
    @field_validator('redirect_uri')
    @classmethod
    def validate_redirect_uri(cls, v):
        """Validate redirect URI format."""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError("redirect_uri must start with http:// or https://")
            # Basic URL validation
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v):
                raise ValueError("redirect_uri must be a valid URL")
        return v


class AuthCallbackRequest(BaseModel):
    """Request model for authentication callback endpoint."""
    
    code: str = Field(
        ...,
        description="Authorization code from Google OAuth",
        min_length=1,
        max_length=2048
    )
    
    state: Optional[str] = Field(
        None,
        description="State parameter containing redirect URI and callback URL",
        max_length=4096
    )
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """Validate authorization code format."""
        if not v or not v.strip():
            raise ValueError("Authorization code cannot be empty")
        return v.strip()
