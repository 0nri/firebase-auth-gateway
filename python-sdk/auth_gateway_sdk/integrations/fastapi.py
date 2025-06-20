"""
FastAPI integration helpers for Auth Gateway SDK.

This module provides FastAPI-specific utilities to simplify integration
with the Auth Gateway service, including dependency injection, middleware,
and route helpers.
"""
import logging
from typing import Optional, Callable, List
from fastapi import Depends, HTTPException, Request, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
import asyncio

from ..client import AuthGatewayClient
from ..config import AuthGatewayConfig
from ..models import UserData, LoginResponse, LoginRequest
from ..exceptions import (
    AuthGatewayException,
    AuthenticationError,
    TokenExpiredError,
    TokenInvalidError,
    DomainNotAllowedError,
    NetworkError,
)

logger = logging.getLogger(__name__)

# Global security scheme for Bearer token extraction
security = HTTPBearer(auto_error=False)


class AuthGatewayFastAPI:
    """
    FastAPI integration helper for Auth Gateway.
    
    This class provides convenient methods and dependencies for integrating
    Auth Gateway authentication into FastAPI applications.
    """
    
    def __init__(
        self, 
        config: Optional[AuthGatewayConfig] = None,
        base_url: Optional[str] = None,
        auto_error: bool = True
    ):
        """
        Initialize FastAPI Auth Gateway integration.
        
        Args:
            config: Auth Gateway configuration
            base_url: Simple base URL (alternative to full config)
            auto_error: Whether to automatically raise HTTPException on auth errors
        """
        if base_url and not config:
            config = AuthGatewayConfig.from_url(base_url)
        
        self.client = AuthGatewayClient(config)
        self.auto_error = auto_error
        
        # Create bound dependency functions
        self._current_user_optional = self._create_current_user_dependency(required=False)
        self._current_user_required = self._create_current_user_dependency(required=True)
    
    def _create_current_user_dependency(self, required: bool = True) -> Callable:
        """Create a dependency function for getting current user."""
        
        async def get_current_user(
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
            request: Request = None
        ) -> Optional[UserData]:
            """
            Dependency to get current authenticated user.
            
            Returns:
                UserData if authenticated, None if not (when required=False)
                
            Raises:
                HTTPException: If authentication fails and required=True
            """
            token = None
            
            # Try to get token from Authorization header
            if credentials:
                token = credentials.credentials
            
            # Fallback: try to get token from cookies
            if not token and request:
                token = request.cookies.get("access_token")
            
            # If no token and not required, return None
            if not token:
                if required and self.auto_error:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
            
            # Verify token
            try:
                user = await self.client.verify_token(token)
                logger.debug(f"User authenticated: {user.email}")
                return user
                
            except TokenExpiredError as e:
                logger.warning(f"Token expired: {e.message}")
                if required and self.auto_error:
                    raise HTTPException(
                        status_code=401,
                        detail="Token expired",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
                
            except TokenInvalidError as e:
                logger.warning(f"Invalid token: {e.message}")
                if required and self.auto_error:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid token",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
                
            except DomainNotAllowedError as e:
                logger.warning(f"Domain not allowed: {e.message}")
                if required and self.auto_error:
                    raise HTTPException(
                        status_code=403,
                        detail="Email domain not allowed"
                    )
                return None
                
            except AuthenticationError as e:
                logger.warning(f"Authentication error: {e.message}")
                if required and self.auto_error:
                    raise HTTPException(
                        status_code=401,
                        detail=e.message,
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
                
            except NetworkError as e:
                logger.error(f"Network error during token verification: {e.message}")
                if required and self.auto_error:
                    raise HTTPException(
                        status_code=503,
                        detail="Authentication service unavailable"
                    )
                return None
                
            except AuthGatewayException as e:
                logger.error(f"Auth Gateway error: {e.message}")
                if required and self.auto_error:
                    raise HTTPException(
                        status_code=500,
                        detail="Authentication service error"
                    )
                return None
        
        return get_current_user
    
    def get_current_user(self) -> Callable:
        """
        Get dependency that requires user authentication.
        
        Returns:
            Dependency function that returns UserData or raises HTTPException
        """
        return self._current_user_required
    
    def get_current_user_optional(self) -> Callable:
        """
        Get dependency for optional user authentication.
        
        Returns:
            Dependency function that returns UserData or None
        """
        return self._current_user_optional
    
    async def generate_login_url(self, redirect_uri: Optional[str] = None) -> LoginResponse:
        """Generate login URL."""
        return await self.client.generate_login_url(redirect_uri)
    
    def create_auth_routes(
        self, 
        prefix: str = "/auth",
        tags: Optional[List[str]] = None,
        login_redirect_uri: Optional[str] = None
    ) -> APIRouter:
        """
        Create authentication routes.
        
        Args:
            prefix: URL prefix for auth routes
            tags: OpenAPI tags for the routes
            login_redirect_uri: Default redirect URI for login
            
        Returns:
            APIRouter with authentication routes
        """
        router = APIRouter(prefix=prefix, tags=tags or ["authentication"])
        
        # Create dependencies outside of route handlers to avoid capturing issues
        auth_required = self.get_current_user()
        auth_optional = self.get_current_user_optional()
        
        # Store reference to avoid closure issues
        client = self.client
        
        # Login route - POST to match backend API
        async def login_handler_post(request: LoginRequest):
            """Generate login URL via backend API (JSON response)."""
            try:
                uri = request.redirect_uri or login_redirect_uri
                response = await client.generate_login_url(uri)
                return response  # Return JSON response
            except Exception as e:
                logger.error(f"Login URL generation failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")
        
        # Login route - GET for browser redirects
        async def login_handler_get(redirect_uri: Optional[str] = None):
            """Initiate login by redirecting to Google OAuth."""
            try:
                uri = redirect_uri or login_redirect_uri
                response = await client.generate_login_url(uri)
                return RedirectResponse(url=response.url)
            except Exception as e:
                logger.error(f"Login URL generation failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")
        
        # Logout route
        async def logout_handler():
            """Logout by clearing cookies."""
            try:
                response = RedirectResponse(url="/")
                response.delete_cookie("access_token")
                return response
            except Exception as e:
                logger.error(f"Logout failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")
        
        # Me route
        async def me_handler(user: UserData = Depends(auth_required)):
            """Get current user information."""
            return user
        
        # Status route
        async def status_handler(user: Optional[UserData] = Depends(auth_optional)):
            """Check authentication status."""
            return {
                "authenticated": user is not None,
                "user": user
            }
        
        # Add routes to router
        router.add_api_route("/login", login_handler_post, methods=["POST"], summary="Generate login URL (API)")
        router.add_api_route("/login", login_handler_get, methods=["GET"], summary="Initiate login (Browser)")
        router.add_api_route("/logout", logout_handler, methods=["GET"], summary="Logout")
        router.add_api_route("/me", me_handler, methods=["GET"], summary="Get current user")
        router.add_api_route("/status", status_handler, methods=["GET"], summary="Check auth status")
        
        return router
    
    async def close(self):
        """Close the underlying client."""
        await self.client.close()


# Standalone dependency functions for simple use cases
def create_auth_dependency(
    client: AuthGatewayClient, 
    required: bool = True,
    auto_error: bool = True
) -> Callable:
    """
    Create a standalone authentication dependency.
    
    Args:
        client: Auth Gateway client instance
        required: Whether authentication is required
        auto_error: Whether to raise HTTPException on auth errors
        
    Returns:
        Dependency function
    """
    async def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        request: Request = None
    ) -> Optional[UserData]:
        token = None
        
        if credentials:
            token = credentials.credentials
        elif request:
            token = request.cookies.get("access_token")
        
        if not token:
            if required and auto_error:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        try:
            return await client.verify_token(token)
        except AuthenticationError as e:
            if required and auto_error:
                raise HTTPException(
                    status_code=401,
                    detail=e.message,
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        except AuthGatewayException as e:
            if required and auto_error:
                raise HTTPException(status_code=500, detail="Authentication error")
            return None
    
    return get_current_user


# Convenience functions for common patterns
def get_auth_client(base_url: str) -> AuthGatewayClient:
    """Get a configured Auth Gateway client."""
    return AuthGatewayClient(base_url)


def setup_auth_middleware(app, client: AuthGatewayClient):
    """
    Add middleware to extract tokens from cookies and add to request headers.
    
    This middleware helps integrate cookie-based auth with Bearer token dependencies.
    """
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Extract token from cookies and add to headers if not already present
        if "authorization" not in request.headers:
            token = request.cookies.get("access_token")
            if token:
                # Create a mutable headers dict
                headers = dict(request.headers)
                headers["authorization"] = f"Bearer {token}"
                
                # Update the request scope
                request.scope["headers"] = [
                    (k.encode(), v.encode()) for k, v in headers.items()
                ]
        
        return await call_next(request)
