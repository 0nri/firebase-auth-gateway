"""
Pydantic models for Auth Gateway SDK.

These models mirror the backend models to ensure 100% API compatibility.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class UserData(BaseModel):
    """User data model for authenticated users."""
    
    uid: str = Field(..., description="Unique user identifier from Firebase")
    email: str = Field(..., description="User email address")
    display_name: Optional[str] = Field(None, description="User display name")
    photo_url: Optional[str] = Field(None, description="User profile photo URL")


class LoginRequest(BaseModel):
    """Request model for login endpoint."""
    
    redirect_uri: Optional[str] = Field(
        None,
        description="Client application redirect URI after successful authentication"
    )


class LoginResponse(BaseModel):
    """Response model for login endpoint."""
    
    url: str = Field(..., description="Google authentication URL for user redirect")


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


class AuthCallbackResponse(BaseModel):
    """Response model for authentication callback endpoint."""
    
    token: str = Field(..., description="Firebase ID token for authenticated user")
    user: UserData = Field(..., description="Authenticated user data")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class LogoutResponse(BaseModel):
    """Response model for logout endpoint."""
    
    status: str = Field(..., description="Logout status")
    message: Optional[str] = Field(None, description="Logout message")
