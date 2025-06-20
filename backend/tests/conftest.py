"""
Pytest configuration and fixtures for Auth Gateway tests.
"""
import pytest
import os
from unittest.mock import Mock, patch

# Set up test environment variables before any imports
os.environ.update({
    "FIREBASE_API_KEY": "test-api-key",
    "FIREBASE_AUTH_DOMAIN": "test-project.firebaseapp.com", 
    "FIREBASE_PROJECT_ID": "test-project",
    "GOOGLE_CLIENT_ID": "test-client-id",
    "GOOGLE_CLIENT_SECRET": "test-client-secret",
    "GATEWAY_PUBLIC_URL": "https://test-gateway.com",
    "AUTH_REDIRECT_URL": "https://test-client.com/callback",
    "ALLOWED_EMAIL_DOMAIN_REGEX": ".*@example\.com$",
    "CORS_ALLOWED_ORIGINS": "https://test-client.com",
    "LOG_LEVEL": "DEBUG",
    "ENVIRONMENT": "test"
})

from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app


@pytest.fixture
def test_settings():
    """Test settings with safe values."""
    # Mock environment variables for testing
    import os
    os.environ.update({
        "FIREBASE_API_KEY": "test-api-key",
        "FIREBASE_AUTH_DOMAIN": "test-project.firebaseapp.com", 
        "FIREBASE_PROJECT_ID": "test-project",
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-client-secret",
        "GATEWAY_PUBLIC_URL": "https://test-gateway.com",
        "AUTH_REDIRECT_URL": "https://test-client.com/callback",
        "ALLOWED_EMAIL_DOMAIN_REGEX": ".*@example\.com$",
        "CORS_ALLOWED_ORIGINS": "https://test-client.com",
        "LOG_LEVEL": "DEBUG",
        "ENVIRONMENT": "test"
    })
    
    return Settings(
        firebase_api_key="test-api-key",
        firebase_auth_domain="test-project.firebaseapp.com",
        firebase_project_id="test-project",
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
        gateway_public_url="https://test-gateway.com",
        auth_redirect_url="https://test-client.com/callback",
        allowed_email_domain_regex=".*@example\.com$",
        cors_allowed_origins="https://test-client.com",
        log_level="DEBUG",
        environment="test"
    )


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_firebase_admin():
    """Mock Firebase Admin SDK."""
    with patch('firebase_admin.initialize_app') as mock_init, \
         patch('firebase_admin.get_app') as mock_get_app, \
         patch('firebase_admin.auth.verify_id_token') as mock_verify:
        
        # Mock app initialization
        mock_get_app.side_effect = ValueError("No app")  # First call fails
        mock_init.return_value = Mock()
        
        # Mock token verification
        mock_verify.return_value = {
            "uid": "test-uid-123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg"
        }
        
        yield {
            "init": mock_init,
            "get_app": mock_get_app,
            "verify": mock_verify
        }


@pytest.fixture
def mock_requests():
    """Mock requests library for external API calls."""
    with patch('requests.post') as mock_post:
        # Mock Google token exchange response
        google_response = Mock()
        google_response.ok = True
        google_response.json.return_value = {
            "id_token": "mock-google-id-token",
            "access_token": "mock-access-token"
        }
        google_response.raise_for_status.return_value = None
        
        # Mock Firebase token exchange response  
        firebase_response = Mock()
        firebase_response.ok = True
        firebase_response.json.return_value = {
            "idToken": "mock-firebase-id-token",
            "refreshToken": "mock-refresh-token"
        }
        firebase_response.raise_for_status.return_value = None
        
        # Configure mock to return different responses based on URL
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'oauth2.googleapis.com' in url:
                return google_response
            elif 'identitytoolkit.googleapis.com' in url:
                return firebase_response
            else:
                return Mock()
        
        mock_post.side_effect = side_effect
        yield mock_post


@pytest.fixture
def valid_token_claims():
    """Valid token claims for testing."""
    return {
        "uid": "test-uid-123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
        "iss": "https://securetoken.google.com/test-project",
        "aud": "test-project",
        "auth_time": 1234567890,
        "user_id": "test-uid-123",
        "sub": "test-uid-123",
        "iat": 1234567890,
        "exp": 1234567890 + 3600,
        "email_verified": True,
        "firebase": {
            "identities": {
                "google.com": ["test-google-id"],
                "email": ["test@example.com"]
            },
            "sign_in_provider": "google.com"
        }
    }


@pytest.fixture
def invalid_domain_token_claims():
    """Token claims with invalid domain for testing."""
    return {
        "uid": "test-uid-456",
        "email": "test@invalid.com",
        "name": "Invalid User",
        "picture": "https://example.com/photo.jpg"
    }


@pytest.fixture
def auth_header():
    """Valid authorization header for testing."""
    return "Bearer mock-firebase-id-token"


@pytest.fixture
def invalid_auth_header():
    """Invalid authorization header for testing."""
    return "Invalid token-format"


@pytest.fixture
def google_oauth_callback_params():
    """Google OAuth callback parameters for testing."""
    return {
        "code": "mock-authorization-code",
        "state": '{"redirect_uri": "https://test-client.com/callback", "callback_url": "https://test-gateway.com/auth/callback"}'
    }
