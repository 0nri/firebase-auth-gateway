"""
Tests for AuthService.
"""
import pytest
import json
import urllib.parse
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request
import requests

from app.services.auth_service import AuthService


class TestAuthService:
    """Test cases for AuthService."""
    
    def test_init(self, test_settings):
        """Test AuthService initialization."""
        service = AuthService(test_settings)
        assert service.settings == test_settings
    
    def test_create_google_auth_url_success(self, test_settings):
        """Test successful Google auth URL creation."""
        service = AuthService(test_settings)
        
        url = service.create_google_auth_url("https://client.com/callback")
        
        assert "accounts.google.com/o/oauth2/auth" in url
        assert "client_id=test-client-id" in url
        assert "response_type=code" in url
        assert "scope=email%20profile" in url
        assert "redirect_uri=" in url
        assert "state=" in url
    
    def test_create_google_auth_url_with_default_redirect(self, test_settings):
        """Test Google auth URL creation with default redirect URI."""
        service = AuthService(test_settings)
        
        url = service.create_google_auth_url()
        
        # Should use default redirect URI from settings
        assert "accounts.google.com/o/oauth2/auth" in url
    
    def test_create_google_auth_url_missing_config(self, test_settings):
        """Test Google auth URL creation with missing configuration."""
        test_settings.firebase_api_key = ""
        service = AuthService(test_settings)
        
        with pytest.raises(HTTPException) as exc:
            service.create_google_auth_url("https://client.com/callback")
        
        assert exc.value.status_code == 500
        assert "Authentication configuration missing" in exc.value.detail
    
    def test_create_google_auth_url_no_redirect_uri(self, test_settings):
        """Test Google auth URL creation without redirect URI."""
        test_settings.auth_redirect_url = None
        service = AuthService(test_settings)
        
        with pytest.raises(HTTPException) as exc:
            service.create_google_auth_url()
        
        assert exc.value.status_code == 400
        assert "Client redirect URI not provided" in exc.value.detail
    
    def test_create_google_auth_url_no_gateway_url(self, test_settings):
        """Test Google auth URL creation without gateway public URL."""
        test_settings.gateway_public_url = ""
        service = AuthService(test_settings)
        
        with pytest.raises(HTTPException) as exc:
            service.create_google_auth_url("https://client.com/callback")
        
        assert exc.value.status_code == 500
        assert "Gateway public URL not configured" in exc.value.detail
    
    def test_exchange_code_for_token_success(self, test_settings, mock_requests):
        """Test successful code exchange for token."""
        service = AuthService(test_settings)
        
        result = service.exchange_code_for_token("auth-code", "https://callback.com")
        
        assert result == {"idToken": "mock-firebase-id-token", "refreshToken": "mock-refresh-token"}
        assert mock_requests.call_count == 2  # Google + Firebase calls
    
    def test_exchange_code_for_token_missing_config(self, test_settings):
        """Test code exchange with missing configuration."""
        test_settings.google_client_secret = ""
        service = AuthService(test_settings)
        
        with pytest.raises(HTTPException) as exc:
            service.exchange_code_for_token("auth-code", "https://callback.com")
        
        assert exc.value.status_code == 500
        assert "OAuth configuration missing" in exc.value.detail
    
    def test_exchange_google_code_success(self, test_settings, mock_requests):
        """Test successful Google code exchange."""
        service = AuthService(test_settings)
        
        result = service._exchange_google_code("auth-code", "https://callback.com")
        
        assert result == {"id_token": "mock-google-id-token", "access_token": "mock-access-token"}
    
    def test_exchange_google_code_no_id_token(self, test_settings):
        """Test Google code exchange when no ID token is returned."""
        service = AuthService(test_settings)
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = {"access_token": "token"}  # No id_token
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc:
                service._exchange_google_code("auth-code", "https://callback.com")
            
            assert exc.value.status_code == 500
            assert "Authentication failed" in exc.value.detail
    
    def test_exchange_google_code_timeout(self, test_settings):
        """Test Google code exchange with timeout."""
        service = AuthService(test_settings)
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout()
            
            with pytest.raises(HTTPException) as exc:
                service._exchange_google_code("auth-code", "https://callback.com")
            
            assert exc.value.status_code == 500
            assert "Authentication service timeout" in exc.value.detail
    
    def test_exchange_google_code_request_error(self, test_settings):
        """Test Google code exchange with request error."""
        service = AuthService(test_settings)
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException()
            
            with pytest.raises(HTTPException) as exc:
                service._exchange_google_code("auth-code", "https://callback.com")
            
            assert exc.value.status_code == 500
            assert "Authentication failed" in exc.value.detail
    
    def test_exchange_firebase_token_success(self, test_settings):
        """Test successful Firebase token exchange."""
        service = AuthService(test_settings)
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = {"idToken": "firebase-token"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = service._exchange_firebase_token("google-id-token", "https://callback.com")
            
            assert result == {"idToken": "firebase-token"}
    
    def test_exchange_firebase_token_missing_token(self, test_settings):
        """Test Firebase token exchange with missing Google ID token."""
        service = AuthService(test_settings)
        
        with pytest.raises(HTTPException) as exc:
            service._exchange_firebase_token("", "https://callback.com")
        
        assert exc.value.status_code == 500
        assert "Missing Google ID token" in exc.value.detail
    
    def test_exchange_firebase_token_no_id_token(self, test_settings):
        """Test Firebase token exchange when no ID token is returned."""
        service = AuthService(test_settings)
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = {"refreshToken": "token"}  # No idToken
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc:
                service._exchange_firebase_token("google-id-token", "https://callback.com")
            
            assert exc.value.status_code == 500
            assert "Authentication failed" in exc.value.detail
    
    def test_parse_state_parameter_success(self, test_settings):
        """Test successful state parameter parsing."""
        service = AuthService(test_settings)
        
        state_data = {"redirect_uri": "https://client.com", "callback_url": "https://gateway.com/callback"}
        state = urllib.parse.quote(json.dumps(state_data))
        
        redirect_uri, callback_url = service.parse_state_parameter(state)
        
        assert redirect_uri == "https://client.com"
        assert callback_url == "https://gateway.com/callback"
    
    def test_parse_state_parameter_double_encoded(self, test_settings):
        """Test state parameter parsing with double encoding."""
        service = AuthService(test_settings)
        
        state_data = {"redirect_uri": "https://client.com", "callback_url": "https://gateway.com/callback"}
        # Double encode
        state = urllib.parse.quote(urllib.parse.quote(json.dumps(state_data)))
        
        redirect_uri, callback_url = service.parse_state_parameter(state)
        
        assert redirect_uri == "https://client.com"
        assert callback_url == "https://gateway.com/callback"
    
    def test_parse_state_parameter_none(self, test_settings):
        """Test state parameter parsing with None."""
        service = AuthService(test_settings)
        
        redirect_uri, callback_url = service.parse_state_parameter(None)
        
        assert redirect_uri is None
        assert callback_url is None
    
    def test_parse_state_parameter_invalid_json(self, test_settings):
        """Test state parameter parsing with invalid JSON."""
        service = AuthService(test_settings)
        
        redirect_uri, callback_url = service.parse_state_parameter("invalid-json")
        
        assert redirect_uri is None
        assert callback_url is None
    
    def test_construct_callback_url_from_callback_url(self, test_settings):
        """Test callback URL construction using callback URL from state."""
        service = AuthService(test_settings)
        
        url = service.construct_callback_url(
            "https://client.com", 
            "https://gateway.com/auth/callback"
        )
        
        assert url == "https://gateway.com/auth/callback"
    
    def test_construct_callback_url_from_redirect_uri(self, test_settings):
        """Test callback URL construction using redirect URI."""
        service = AuthService(test_settings)
        
        url = service.construct_callback_url("https://client.com/callback", None)
        
        assert url == "https://client.com/auth/callback"
    
    def test_construct_callback_url_from_request(self, test_settings):
        """Test callback URL construction using request headers."""
        service = AuthService(test_settings)
        
        mock_request = Mock()
        mock_request.headers = {"host": "gateway.com", "x-forwarded-proto": "https"}
        
        url = service.construct_callback_url(None, None, mock_request)
        
        assert url == "https://gateway.com/auth/callback"
    
    def test_construct_callback_url_fallback(self, test_settings):
        """Test callback URL construction with fallback."""
        service = AuthService(test_settings)
        
        url = service.construct_callback_url(None, None, None)
        
        assert url == "https://test-project.firebaseapp.com/auth/callback"
    
    def test_construct_callback_url_error_handling(self, test_settings):
        """Test callback URL construction with error handling."""
        service = AuthService(test_settings)
        
        # Mock an error in URL parsing
        with patch('urllib.parse.urlparse') as mock_parse:
            mock_parse.side_effect = Exception("Parse error")
            
            url = service.construct_callback_url("https://client.com", None)
            
            # Should fall back to Firebase domain
            assert url == "https://test-project.firebaseapp.com/auth/callback"
    
    def test_state_parameter_encoding_in_url(self, test_settings):
        """Test that state parameter is properly encoded in auth URL."""
        service = AuthService(test_settings)
        
        url = service.create_google_auth_url("https://client.com/callback")
        
        # Extract state parameter from URL
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        state_param = query_params['state'][0]
        
        # Decode and verify state parameter
        state_data = json.loads(urllib.parse.unquote(state_param))
        assert state_data['redirect_uri'] == "https://client.com/callback"
        assert state_data['callback_url'] == "https://test-gateway.com/auth/callback"
