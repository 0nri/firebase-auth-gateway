"""
Authentication endpoints for Auth Gateway.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from fastapi.responses import RedirectResponse, HTMLResponse

from ..config import Settings, get_settings
from ..models.requests import LoginRequest, AuthCallbackRequest
from ..models.responses import (
    LoginResponse, 
    AuthCallbackResponse, 
    UserData, 
    LogoutResponse,
    ErrorResponse
)
from ..services import TokenService, DomainService, AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_token_service() -> TokenService:
    """Dependency to get token service instance."""
    return TokenService()


def get_domain_service(settings: Settings = Depends(get_settings)) -> DomainService:
    """Dependency to get domain service instance."""
    return DomainService(settings)


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    """Dependency to get auth service instance."""
    return AuthService(settings)


def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract token from Authorization header."""
    token_service = TokenService()
    return token_service.extract_token_from_header(authorization)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Generate a Google authentication URL."""
    try:
        auth_url = auth_service.create_google_auth_url(request.redirect_uri)
        logger.info("Authentication URL generated successfully")
        return LoginResponse(url=auth_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate authentication URL: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to generate authentication URL")


@router.post("/callback", response_model=AuthCallbackResponse)
async def auth_callback_post(
    request: AuthCallbackRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service),
    domain_service: DomainService = Depends(get_domain_service)
):
    """Handle authentication callback via POST request."""
    try:
        # Parse state parameter
        redirect_uri, callback_url = auth_service.parse_state_parameter(request.state)
        
        # Construct callback URL for token exchange
        request_uri = auth_service.construct_callback_url(
            redirect_uri, callback_url, http_request
        )
        
        # Exchange code for token
        token_data = auth_service.exchange_code_for_token(request.code, request_uri)
        
        # Get ID token
        id_token = token_data.get("idToken")
        if not id_token:
            logger.error("Token exchange succeeded but no ID token returned")
            raise HTTPException(status_code=500, detail="Authentication failed")
        
        # Verify token and extract claims
        decoded_token = token_service.verify_token(id_token)
        token_service.validate_token_claims(decoded_token)
        
        # Extract and validate user data
        user_data_dict = token_service.extract_user_data(decoded_token)
        email = user_data_dict.get("email", "")
        
        # Validate email domain
        domain_service.validate_and_raise(email)
        
        # Create user data response
        user_data = UserData(**user_data_dict)
        
        logger.info("Authentication callback completed successfully")
        return AuthCallbackResponse(token=id_token, user=user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication callback failed: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/callback")
async def auth_callback_get(
    code: str,
    state: Optional[str] = None,
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service),
    domain_service: DomainService = Depends(get_domain_service)
):
    """Handle authentication callback via GET request."""
    try:
        # Parse state parameter
        redirect_uri, callback_url = auth_service.parse_state_parameter(state)
        
        if not redirect_uri:
            logger.warning("Authentication callback failed: invalid state parameter")
            return HTMLResponse(
                "Authentication failed: Invalid state parameter or missing redirect URI",
                status_code=400
            )
        
        # Construct callback URL for token exchange
        request_uri = auth_service.construct_callback_url(
            redirect_uri, callback_url, request
        )
        
        # Exchange code for token
        token_data = auth_service.exchange_code_for_token(code, request_uri)
        
        # Get ID token
        id_token = token_data.get("idToken")
        if not id_token:
            logger.error("Token exchange succeeded but no ID token returned")
            return HTMLResponse("Authentication failed: No ID token received", status_code=500)
        
        # Verify token and validate claims
        decoded_token = token_service.verify_token(id_token)
        token_service.validate_token_claims(decoded_token)
        
        # Extract user data and validate email domain
        user_data_dict = token_service.extract_user_data(decoded_token)
        email = user_data_dict.get("email", "")
        
        # Validate email domain
        if not domain_service.validate_email_domain(email):
            logger.warning("Authentication failed: email domain not allowed")
            return HTMLResponse("Authentication failed: Email domain not allowed", status_code=403)
        
        # Redirect to client application with token
        redirect_url = f"{redirect_uri}?token={id_token}"
        logger.info("Authentication callback GET completed successfully")
        return RedirectResponse(redirect_url)
        
    except HTTPException as e:
        logger.warning(f"Authentication callback GET failed: {e.detail}")
        return HTMLResponse(f"Authentication failed: {e.detail}", status_code=e.status_code)
    except Exception as e:
        logger.error(f"Authentication callback GET failed: {type(e).__name__}")
        return HTMLResponse("Authentication failed", status_code=500)


@router.post("/logout", response_model=LogoutResponse)
async def logout():
    """Handle logout."""
    # Firebase authentication is stateless, so we don't need to do anything server-side
    # The client will handle clearing tokens
    logger.info("Logout request processed")
    return LogoutResponse(status="ok", message="Logout successful")
