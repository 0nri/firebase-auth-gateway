"""
Tests for TokenService.
"""
import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException
from firebase_admin import auth

from app.services.token_service import TokenService


class TestTokenService:
    """Test cases for TokenService."""
    
    def test_init_firebase_not_initialized(self, mock_firebase_admin):
        """Test TokenService initialization when Firebase is not initialized."""
        service = TokenService()
        mock_firebase_admin["init"].assert_called_once()
    
    def test_init_firebase_already_initialized(self):
        """Test TokenService initialization when Firebase is already initialized."""
        with patch('firebase_admin.get_app') as mock_get_app:
            mock_get_app.return_value = Mock()  # App exists
            
            service = TokenService()
            # Should not raise error
            assert service is not None
    
    def test_verify_token_success(self, mock_firebase_admin, valid_token_claims):
        """Test successful token verification."""
        mock_firebase_admin["verify"].return_value = valid_token_claims
        
        service = TokenService()
        result = service.verify_token("valid-token")
        
        assert result == valid_token_claims
        mock_firebase_admin["verify"].assert_called_once_with("valid-token", check_revoked=True)
    
    def test_verify_token_expired(self, mock_firebase_admin):
        """Test token verification with expired token."""
        mock_firebase_admin["verify"].side_effect = auth.ExpiredIdTokenError("Token expired", cause=Exception("Expired"))
        
        service = TokenService()
        
        with pytest.raises(HTTPException) as exc:
            service.verify_token("expired-token")
        
        assert exc.value.status_code == 401
        assert exc.value.detail == "Token expired"
    
    def test_verify_token_revoked(self, mock_firebase_admin):
        """Test token verification with revoked token."""
        mock_firebase_admin["verify"].side_effect = auth.RevokedIdTokenError("Token revoked")
        
        service = TokenService()
        
        with pytest.raises(HTTPException) as exc:
            service.verify_token("revoked-token")
        
        assert exc.value.status_code == 401
        assert exc.value.detail == "Token revoked"
    
    def test_verify_token_invalid(self, mock_firebase_admin):
        """Test token verification with invalid token."""
        mock_firebase_admin["verify"].side_effect = auth.InvalidIdTokenError("Invalid token")
        
        service = TokenService()
        
        with pytest.raises(HTTPException) as exc:
            service.verify_token("invalid-token")
        
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid token"
    
    def test_verify_token_generic_error(self, mock_firebase_admin):
        """Test token verification with generic error."""
        mock_firebase_admin["verify"].side_effect = Exception("Generic error")
        
        service = TokenService()
        
        with pytest.raises(HTTPException) as exc:
            service.verify_token("error-token")
        
        assert exc.value.status_code == 401
        assert exc.value.detail == "Token verification failed"
    
    def test_extract_token_from_header_success(self):
        """Test successful token extraction from header."""
        service = TokenService()
        
        token = service.extract_token_from_header("Bearer valid-token-123")
        
        assert token == "valid-token-123"
    
    def test_extract_token_from_header_missing(self):
        """Test token extraction with missing header."""
        service = TokenService()
        
        with pytest.raises(HTTPException) as exc:
            service.extract_token_from_header(None)
        
        assert exc.value.status_code == 401
        assert "Authorization header missing" in exc.value.detail
    
    def test_extract_token_from_header_invalid_format(self):
        """Test token extraction with invalid header format."""
        service = TokenService()
        
        with pytest.raises(HTTPException) as exc:
            service.extract_token_from_header("Invalid format")
        
        assert exc.value.status_code == 401
        assert "Invalid authorization header format" in exc.value.detail
    
    def test_extract_token_from_header_empty_token(self):
        """Test token extraction with empty token."""
        service = TokenService()
        
        with pytest.raises(HTTPException) as exc:
            service.extract_token_from_header("Bearer ")
        
        assert exc.value.status_code == 401
        assert "Invalid authorization header format" in exc.value.detail
    
    def test_extract_user_data(self, valid_token_claims):
        """Test user data extraction from token claims."""
        service = TokenService()
        
        user_data = service.extract_user_data(valid_token_claims)
        
        expected = {
            "uid": "test-uid-123",
            "email": "test@example.com",
            "display_name": "Test User",
            "photo_url": "https://example.com/photo.jpg"
        }
        assert user_data == expected
    
    def test_extract_user_data_missing_fields(self):
        """Test user data extraction with missing fields."""
        service = TokenService()
        
        incomplete_claims = {"uid": "test-uid"}
        user_data = service.extract_user_data(incomplete_claims)
        
        expected = {
            "uid": "test-uid",
            "email": "",
            "display_name": "",
            "photo_url": ""
        }
        assert user_data == expected
    
    def test_validate_token_claims_success(self, valid_token_claims):
        """Test successful token claims validation."""
        service = TokenService()
        
        # Should not raise any exception
        service.validate_token_claims(valid_token_claims)
    
    def test_validate_token_claims_missing_uid(self):
        """Test token claims validation with missing UID."""
        service = TokenService()
        
        invalid_claims = {"email": "test@example.com"}
        
        with pytest.raises(HTTPException) as exc:
            service.validate_token_claims(invalid_claims)
        
        assert exc.value.status_code == 401
        assert "Token missing required user information" in exc.value.detail
    
    def test_validate_token_claims_missing_email(self):
        """Test token claims validation with missing email."""
        service = TokenService()
        
        invalid_claims = {"uid": "test-uid-123"}
        
        with pytest.raises(HTTPException) as exc:
            service.validate_token_claims(invalid_claims)
        
        assert exc.value.status_code == 401
        assert "Token missing required user information" in exc.value.detail
    
    def test_validate_token_claims_empty_values(self):
        """Test token claims validation with empty required values."""
        service = TokenService()
        
        invalid_claims = {"uid": "", "email": ""}
        
        with pytest.raises(HTTPException) as exc:
            service.validate_token_claims(invalid_claims)
        
        assert exc.value.status_code == 401
        assert "Token missing required user information" in exc.value.detail
