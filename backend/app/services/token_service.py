"""
Token verification and management service.
"""
import logging
from typing import Dict, Any
from fastapi import HTTPException
import firebase_admin
from firebase_admin import auth

logger = logging.getLogger(__name__)


class TokenService:
    """Service for Firebase token verification and management."""
    
    def __init__(self):
        """Initialize token service."""
        self._ensure_firebase_initialized()
    
    def _ensure_firebase_initialized(self) -> None:
        """Ensure Firebase Admin SDK is initialized."""
        try:
            firebase_admin.get_app()
        except ValueError:
            # App not initialized yet
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return decoded claims.
        
        Args:
            token: Firebase ID token to verify
            
        Returns:
            Dictionary containing decoded token claims
            
        Raises:
            HTTPException: If token verification fails
        """
        try:
            decoded_token = auth.verify_id_token(token, check_revoked=True)
            logger.debug("Token verification successful")
            return decoded_token
        except auth.ExpiredIdTokenError:
            logger.warning("Token verification failed: token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except auth.RevokedIdTokenError:
            logger.warning("Token verification failed: token revoked")
            raise HTTPException(status_code=401, detail="Token revoked")
        except auth.InvalidIdTokenError:
            logger.warning("Token verification failed: invalid token")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Token verification failed: {type(e).__name__}")
            raise HTTPException(status_code=401, detail="Token verification failed")
    
    def extract_token_from_header(self, authorization: str) -> str:
        """
        Extract token from Authorization header.
        
        Args:
            authorization: Authorization header value
            
        Returns:
            Extracted bearer token
            
        Raises:
            HTTPException: If header format is invalid
        """
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401, 
                detail="Invalid authorization header format. Expected: Bearer <token>"
            )
        
        token = parts[1]
        if not token:
            raise HTTPException(status_code=401, detail="Token cannot be empty")
        
        return token
    
    def extract_user_data(self, decoded_token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user data from decoded token claims.
        
        Args:
            decoded_token: Decoded Firebase token claims
            
        Returns:
            Dictionary containing user data
        """
        return {
            "uid": decoded_token.get("uid", ""),
            "email": decoded_token.get("email", ""),
            "display_name": decoded_token.get("name", ""),
            "photo_url": decoded_token.get("picture", "")
        }
    
    def validate_token_claims(self, decoded_token: Dict[str, Any]) -> None:
        """
        Validate required token claims.
        
        Args:
            decoded_token: Decoded Firebase token claims
            
        Raises:
            HTTPException: If required claims are missing
        """
        required_claims = ["uid", "email"]
        missing_claims = [claim for claim in required_claims if not decoded_token.get(claim)]
        
        if missing_claims:
            logger.warning(f"Token missing required claims: {missing_claims}")
            raise HTTPException(
                status_code=401, 
                detail="Token missing required user information"
            )
