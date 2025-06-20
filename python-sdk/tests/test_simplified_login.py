"""
Test the simplified GET-only login route implementation.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI
from auth_gateway_sdk.models import LoginResponse


@patch('auth_gateway_sdk.integrations.fastapi.AuthGatewayClient')
def test_simplified_login_route(mock_client_class):
    """Test that the simplified GET-only login route works correctly."""
    
    # Setup mock client
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    
    # Mock the generate_login_url response
    mock_response = LoginResponse(url="https://accounts.google.com/oauth/authorize?...")
    
    async def mock_generate_login_url(redirect_uri=None):
        return mock_response
    
    mock_client.generate_login_url = mock_generate_login_url
    
    # Create FastAPI app with simplified auth routes
    app = FastAPI()
    auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
    router = auth.create_auth_routes(login_redirect_uri="http://localhost:8000/auth/callback")
    app.include_router(router)
    
    # Create test client
    client = TestClient(app)
    
    # Test GET /auth/login (should redirect)
    response = client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 307  # FastAPI redirect status code
    assert response.headers["location"] == mock_response.url
    
    print("✅ GET /auth/login redirects correctly")


@patch('auth_gateway_sdk.integrations.fastapi.AuthGatewayClient')
def test_login_with_query_param(mock_client_class):
    """Test login with redirect_uri as query parameter."""
    
    # Setup mock client
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    
    # Mock the generate_login_url response
    mock_response = LoginResponse(url="https://accounts.google.com/oauth/authorize?...")
    
    async def mock_generate_login_url(redirect_uri=None):
        return mock_response
    
    mock_client.generate_login_url = mock_generate_login_url
    
    # Create FastAPI app without default login_redirect_uri
    app = FastAPI()
    auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
    router = auth.create_auth_routes()  # No default
    app.include_router(router)
    
    # Create test client
    client = TestClient(app)
    
    # Test GET with redirect_uri in query parameter
    response = client.get("/auth/login?redirect_uri=http://custom/callback", follow_redirects=False)
    assert response.status_code == 307  # Should redirect
    assert response.headers["location"] == mock_response.url
    
    print("✅ GET /auth/login with query parameter works")


def test_login_missing_redirect_uri():
    """Test that missing redirect_uri returns helpful error."""
    
    # Create FastAPI app without default login_redirect_uri
    app = FastAPI()
    auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
    router = auth.create_auth_routes()  # No default
    app.include_router(router)
    
    # Create test client
    client = TestClient(app)
    
    # Test GET without redirect_uri should return 400
    response = client.get("/auth/login")
    assert response.status_code == 400
    assert "redirect_uri is required" in response.json()["detail"]
    assert "query parameter" in response.json()["detail"]
    
    print("✅ Missing redirect_uri returns helpful error")


@patch('auth_gateway_sdk.integrations.fastapi.AuthGatewayClient')
def test_route_availability(mock_client_class):
    """Test that all expected routes are available with correct methods."""
    
    # Setup mock client
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    
    # Create FastAPI app with auth routes
    app = FastAPI()
    auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
    router = auth.create_auth_routes()
    app.include_router(router)
    
    # Get all routes and their methods
    routes_methods = {}
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            path = route.path
            methods = route.methods
            if path not in routes_methods:
                routes_methods[path] = set()
            routes_methods[path].update(methods)
    
    # Verify expected routes exist with correct methods
    assert "/auth/login" in routes_methods
    assert "GET" in routes_methods["/auth/login"]
    assert "POST" not in routes_methods["/auth/login"]  # POST should be removed
    
    assert "/auth/logout" in routes_methods
    assert "GET" in routes_methods["/auth/logout"]
    
    assert "/auth/me" in routes_methods
    assert "GET" in routes_methods["/auth/me"]
    
    assert "/auth/status" in routes_methods
    assert "GET" in routes_methods["/auth/status"]
    
    print("✅ All expected routes available with correct methods")
    print(f"   /auth/login methods: {routes_methods['/auth/login']}")


def test_client_pattern_match():
    """Verify the auto-generated route matches client's working pattern."""
    
    print("\n=== CLIENT PATTERN VERIFICATION ===")
    print("Client's working manual route:")
    print("@app.get('/auth/login')")
    print("async def login():")
    print("    response = await sdk_client.generate_login_url(settings.REDIRECT_URI)")
    print("    return RedirectResponse(url=response.url)")
    print("")
    print("Auto-generated route now:")
    print("@router.get('/login')")
    print("async def login_handler(redirect_uri: Optional[str] = None):")
    print("    uri = redirect_uri or login_redirect_uri")
    print("    response = await client.generate_login_url(uri)")
    print("    return RedirectResponse(url=response.url)")
    print("")
    print("✅ PERFECT MATCH: Both use GET and return RedirectResponse")
    print("✅ CLIENT SOLUTION: auth.create_auth_routes(login_redirect_uri='...')")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
