"""
Authentication service for handling OAuth flows and token exchange.
"""
import json
import logging
import urllib.parse
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException, Request
import requests

from ..config import Settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling Google OAuth authentication flow."""
    
    def __init__(self, settings: Settings):
        """
        Initialize authentication service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
    
    def create_google_auth_url(self, redirect_uri: Optional[str] = None) -> str:
        """
        Create a Google authentication URL.
        
        Args:
            redirect_uri: Client application redirect URI
            
        Returns:
            Google OAuth authentication URL
            
        Raises:
            HTTPException: If configuration is missing or invalid
        """
        # Validate configuration
        if not self.settings.firebase_api_key or not self.settings.google_client_id:
            raise HTTPException(status_code=500, detail="Authentication configuration missing")
        
        # Use provided redirect URI or default
        final_redirect = redirect_uri or self.settings.auth_redirect_url
        if not final_redirect:
            raise HTTPException(
                status_code=400, 
                detail="Client redirect URI not provided and no default configured"
            )
        
        if not self.settings.gateway_public_url:
            raise HTTPException(
                status_code=500, 
                detail="Gateway public URL not configured"
            )
        
        # The callback URL for Google MUST point back to this gateway service
        callback_url = f"{self.settings.gateway_public_url}/auth/callback"
        logger.debug("Creating Google OAuth URL with gateway callback")
        
        # Store the original client redirect URI and gateway callback URL in state
        state_data = {
            "redirect_uri": final_redirect,
            "callback_url": callback_url
        }
        state_raw = json.dumps(state_data)
        
        # Build Google OAuth URL
        base_url = "https://accounts.google.com/o/oauth2/auth"
        
        # Create parameters dictionary
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "email profile"
        }
        
        # Build query string, encoding each parameter
        query_params = [f"{k}={urllib.parse.quote(v)}" for k, v in params.items()]
        
        # Add state parameter with proper encoding
        query_params.append(f"state={urllib.parse.quote(state_raw)}")
        
        # Join all parameters
        query_string = "&".join(query_params)
        
        return f"{base_url}?{query_string}"
    
    def exchange_code_for_token(self, code: str, request_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchange Google authorization code for Firebase token.
        
        Args:
            code: Google authorization code
            request_uri: The callback URI used in the request
            
        Returns:
            Firebase token data
            
        Raises:
            HTTPException: If token exchange fails
        """
        # Validate configuration
        if not all([self.settings.firebase_api_key, self.settings.google_client_id, 
                   self.settings.google_client_secret]):
            raise HTTPException(status_code=500, detail="OAuth configuration missing")
        
        # Step 1: Exchange Google Auth Code for Google Tokens
        google_token_data = self._exchange_google_code(code, request_uri)
        
        # Step 2: Exchange Google ID Token for Firebase Token
        firebase_token_data = self._exchange_firebase_token(
            google_token_data.get("id_token"), 
            request_uri
        )
        
        return firebase_token_data
    
    def _exchange_google_code(self, code: str, request_uri: Optional[str]) -> Dict[str, Any]:
        """
        Exchange Google authorization code for Google tokens.
        
        Args:
            code: Google authorization code
            request_uri: The callback URI used in the request
            
        Returns:
            Google token response data
            
        Raises:
            HTTPException: If exchange fails
        """
        google_token_url = "https://oauth2.googleapis.com/token"
        google_payload = {
            'code': code,
            'client_id': self.settings.google_client_id,
            'client_secret': self.settings.google_client_secret,
            'redirect_uri': request_uri,
            'grant_type': 'authorization_code'
        }
        
        logger.debug("Exchanging Google authorization code")
        
        try:
            response = requests.post(google_token_url, data=google_payload, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            
            if "id_token" not in token_data:
                logger.error("Google token exchange succeeded but no ID token returned")
                raise HTTPException(
                    status_code=500, 
                    detail="Authentication failed: Invalid response from Google"
                )
            
            logger.debug("Google token exchange successful")
            return token_data
            
        except requests.exceptions.Timeout:
            logger.error("Google token exchange timed out")
            raise HTTPException(status_code=500, detail="Authentication service timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Google token exchange failed: {type(e).__name__}")
            raise HTTPException(status_code=500, detail="Authentication failed")
        except Exception as e:
            logger.error(f"Unexpected error during Google token exchange: {type(e).__name__}")
            raise HTTPException(status_code=500, detail="Authentication failed")
    
    def _exchange_firebase_token(self, google_id_token: str, request_uri: Optional[str]) -> Dict[str, Any]:
        """
        Exchange Google ID token for Firebase token.
        
        Args:
            google_id_token: Google ID token
            request_uri: The callback URI used in the request
            
        Returns:
            Firebase token response data
            
        Raises:
            HTTPException: If exchange fails
        """
        if not google_id_token:
            raise HTTPException(status_code=500, detail="Authentication failed: Missing Google ID token")
        
        firebase_token_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={self.settings.firebase_api_key}"
        
        # Construct the postBody required by Firebase signInWithIdp
        firebase_payload_postbody = f"id_token={google_id_token}&providerId=google.com"
        
        firebase_payload = {
            "postBody": firebase_payload_postbody,
            "requestUri": request_uri,
            "returnIdpCredential": False,
            "returnSecureToken": True
        }
        
        logger.debug("Exchanging Google ID token for Firebase token")
        
        try:
            response = requests.post(firebase_token_url, data=firebase_payload, timeout=30)
            response.raise_for_status()
            firebase_data = response.json()
            
            if "idToken" not in firebase_data:
                logger.error("Firebase token exchange succeeded but no ID token returned")
                raise HTTPException(
                    status_code=500, 
                    detail="Authentication failed: Invalid response from Firebase"
                )
            
            logger.debug("Firebase token exchange successful")
            return firebase_data
            
        except requests.exceptions.Timeout:
            logger.error("Firebase token exchange timed out")
            raise HTTPException(status_code=500, detail="Authentication service timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Firebase token exchange failed: {type(e).__name__}")
            raise HTTPException(status_code=500, detail="Authentication failed")
        except Exception as e:
            logger.error(f"Unexpected error during Firebase token exchange: {type(e).__name__}")
            raise HTTPException(status_code=500, detail="Authentication failed")
    
    def parse_state_parameter(self, state: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse state parameter to extract redirect URI and callback URL.
        
        Args:
            state: State parameter from OAuth callback
            
        Returns:
            Tuple of (redirect_uri, callback_url)
        """
        if not state:
            return None, None
        
        try:
            # First attempt - normal decoding
            try:
                state_data = json.loads(urllib.parse.unquote(state))
                logger.debug("State parameter decoded successfully")
            except json.JSONDecodeError:
                # Try double decoding for backward compatibility
                logger.debug("Attempting double-decode of state parameter")
                state_data = json.loads(urllib.parse.unquote(urllib.parse.unquote(state)))
                logger.debug("State parameter double-decoded successfully")
            
            redirect_uri = state_data.get("redirect_uri")
            callback_url = state_data.get("callback_url")
            
            return redirect_uri, callback_url
            
        except Exception as e:
            logger.warning(f"Failed to parse state parameter: {type(e).__name__}")
            return None, None
    
    def construct_callback_url(self, redirect_uri: Optional[str], callback_url: Optional[str], 
                             request: Optional[Request] = None) -> str:
        """
        Construct the callback URL for token exchange.
        
        Args:
            redirect_uri: Client redirect URI from state
            callback_url: Gateway callback URL from state
            request: FastAPI request object for fallback
            
        Returns:
            Constructed callback URL
        """
        try:
            # Use callback_url from state if available
            if callback_url:
                logger.debug("Using callback URL from state")
                return callback_url
            
            # Construct from redirect_uri
            if redirect_uri:
                parsed_uri = urllib.parse.urlparse(redirect_uri)
                constructed_url = f"{parsed_uri.scheme}://{parsed_uri.netloc}/auth/callback"
                logger.debug("Constructed callback URL from redirect URI")
                return constructed_url
            
            # Fallback to request headers
            if request:
                host = request.headers.get("host", "")
                scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
                fallback_url = f"{scheme}://{host}/auth/callback"
                logger.debug("Using fallback callback URL from request headers")
                return fallback_url
            
            # Last resort: use Firebase auth domain
            fallback_url = f"https://{self.settings.firebase_auth_domain}/auth/callback"
            logger.debug("Using Firebase auth domain as callback URL fallback")
            return fallback_url
            
        except Exception as e:
            logger.error(f"Error constructing callback URL: {type(e).__name__}")
            # Last resort fallback
            return f"https://{self.settings.firebase_auth_domain}/auth/callback"
