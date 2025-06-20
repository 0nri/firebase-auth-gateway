"""
Core HTTP client for Auth Gateway SDK.
"""
import asyncio
import logging
from typing import Optional, Union
import httpx
from pydantic import ValidationError

from .config import AuthGatewayConfig, get_default_config
from .models import LoginRequest, LoginResponse, UserData, HealthResponse, LogoutResponse
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

logger = logging.getLogger(__name__)


class AuthGatewayClient:
    """
    Async HTTP client for Auth Gateway API.
    
    This client provides methods to interact with the Auth Gateway service,
    including login URL generation, token verification, and health checks.
    """
    
    def __init__(self, config: Union[str, AuthGatewayConfig, None] = None):
        """
        Initialize the Auth Gateway client.
        
        Args:
            config: Configuration for the client. Can be:
                - str: Base URL of the Auth Gateway
                - AuthGatewayConfig: Full configuration object
                - None: Use environment variables or raise error
        
        Raises:
            ConfigurationError: If configuration is invalid or missing
        """
        if isinstance(config, str):
            self.config = AuthGatewayConfig.from_url(config)
        elif isinstance(config, AuthGatewayConfig):
            self.config = config
        elif config is None:
            self.config = get_default_config()
            if self.config is None:
                raise ConfigurationError(
                    "No configuration provided. Either pass a base_url, "
                    "AuthGatewayConfig object, or set AUTH_GATEWAY_URL environment variable."
                )
        else:
            raise ConfigurationError(f"Invalid config type: {type(config)}")
        
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                follow_redirects=True,
            )
        return self._client
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with error handling and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for httpx request
        
        Returns:
            HTTP response
            
        Raises:
            NetworkError: For network/HTTP errors
            RateLimitError: For rate limiting errors
            AuthGatewayException: For other API errors
        """
        client = await self._get_client()
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(self.config.retry_attempts + 1):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                response = await client.request(method, url, **kwargs)
                
                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < self.config.retry_attempts:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise RateLimitError("Rate limit exceeded", status_code=429)
                
                return response
                
            except httpx.TimeoutException as e:
                if attempt < self.config.retry_attempts:
                    logger.warning(f"Request timeout, retrying... (attempt {attempt + 1})")
                    continue
                raise NetworkError(f"Request timeout: {str(e)}")
            
            except httpx.NetworkError as e:
                if attempt < self.config.retry_attempts:
                    logger.warning(f"Network error, retrying... (attempt {attempt + 1})")
                    continue
                raise NetworkError(f"Network error: {str(e)}")
        
        # This should never be reached due to the loop logic above
        raise NetworkError("Max retries exceeded")
    
    def _handle_error_response(self, response: httpx.Response) -> None:
        """
        Handle error responses from the API.
        
        Args:
            response: HTTP response object
            
        Raises:
            Appropriate exception based on status code and response content
        """
        if response.status_code < 400:
            return
        
        try:
            error_data = response.json()
            message = error_data.get("message", "Unknown error")
            details = error_data.get("details", {})
        except Exception:
            message = f"HTTP {response.status_code}: {response.text[:200]}"
            details = {}
        
        if response.status_code == 401:
            if "expired" in message.lower():
                raise TokenExpiredError(message, status_code=401, details=details)
            elif "invalid" in message.lower():
                raise TokenInvalidError(message, status_code=401, details=details)
            else:
                raise AuthenticationError(message, status_code=401, details=details)
        elif response.status_code == 403:
            if "domain" in message.lower():
                raise DomainNotAllowedError(message, status_code=403, details=details)
            else:
                raise AuthenticationError(message, status_code=403, details=details)
        elif response.status_code == 429:
            raise RateLimitError(message, status_code=429, details=details)
        else:
            raise AuthGatewayException(message, status_code=response.status_code, details=details)
    
    async def generate_login_url(self, redirect_uri: Optional[str] = None) -> LoginResponse:
        """
        Generate a Google authentication URL.
        
        Args:
            redirect_uri: Where to redirect after successful authentication
            
        Returns:
            LoginResponse containing the authentication URL
            
        Raises:
            AuthGatewayException: If the request fails
        """
        request_data = LoginRequest(redirect_uri=redirect_uri)
        
        response = await self._make_request(
            "POST",
            "/auth/login",
            json=request_data.model_dump(exclude_none=True)
        )
        
        self._handle_error_response(response)
        
        try:
            return LoginResponse.model_validate(response.json())
        except ValidationError as e:
            raise AuthGatewayException(f"Invalid response format: {e}")
    
    async def verify_token(self, token: str) -> UserData:
        """
        Verify a Firebase ID token and get user data.
        
        Args:
            token: Firebase ID token to verify
            
        Returns:
            UserData for the authenticated user
            
        Raises:
            AuthenticationError: If token is invalid, expired, or domain not allowed
            AuthGatewayException: If the request fails
        """
        if not token:
            raise TokenInvalidError("Token cannot be empty")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await self._make_request("POST", "/verify-token", headers=headers)
        
        self._handle_error_response(response)
        
        try:
            return UserData.model_validate(response.json())
        except ValidationError as e:
            raise AuthGatewayException(f"Invalid response format: {e}")
    
    async def health_check(self) -> HealthResponse:
        """
        Check the health of the Auth Gateway service.
        
        Returns:
            HealthResponse with service status
            
        Raises:
            AuthGatewayException: If the request fails
        """
        response = await self._make_request("GET", "/health")
        
        self._handle_error_response(response)
        
        try:
            return HealthResponse.model_validate(response.json())
        except ValidationError as e:
            raise AuthGatewayException(f"Invalid response format: {e}")
    
    async def logout(self) -> LogoutResponse:
        """
        Logout (stateless operation).
        
        Returns:
            LogoutResponse confirming logout
            
        Note:
            Since Firebase auth is stateless, this is mainly for API consistency.
            Clients should clear their stored tokens.
        """
        response = await self._make_request("POST", "/auth/logout")
        
        self._handle_error_response(response)
        
        try:
            return LogoutResponse.model_validate(response.json())
        except ValidationError as e:
            raise AuthGatewayException(f"Invalid response format: {e}")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class SyncAuthGatewayClient:
    """
    Synchronous wrapper around AuthGatewayClient for non-async applications.
    """
    
    def __init__(self, config: Union[str, AuthGatewayConfig, None] = None):
        """Initialize synchronous client."""
        self._async_client = AuthGatewayClient(config)
    
    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    def generate_login_url(self, redirect_uri: Optional[str] = None) -> LoginResponse:
        """Synchronous version of generate_login_url."""
        return self._run_async(self._async_client.generate_login_url(redirect_uri))
    
    def verify_token(self, token: str) -> UserData:
        """Synchronous version of verify_token."""
        return self._run_async(self._async_client.verify_token(token))
    
    def health_check(self) -> HealthResponse:
        """Synchronous version of health_check."""
        return self._run_async(self._async_client.health_check())
    
    def logout(self) -> LogoutResponse:
        """Synchronous version of logout."""
        return self._run_async(self._async_client.logout())
    
    def close(self) -> None:
        """Close the client."""
        self._run_async(self._async_client.close())
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
