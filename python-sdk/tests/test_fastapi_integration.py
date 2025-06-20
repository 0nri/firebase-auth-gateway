"""
Tests for FastAPI integration functionality.
"""
import pytest
import signal
import asyncio
from unittest.mock import Mock, patch
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI
from auth_gateway_sdk.config import AuthGatewayConfig


class TestCreateAuthRoutes:
    """Test the create_auth_routes method that has been reported as hanging."""
    
    def test_create_auth_routes_does_not_hang(self):
        """Test that create_auth_routes() completes within reasonable time."""
        def timeout_handler(signum, frame):
            pytest.fail("create_auth_routes() hung for more than 5 seconds")
        
        # Set up timeout handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)  # 5 second timeout
        
        try:
            # This should complete quickly
            auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
            router = auth.create_auth_routes()
            
            # Verify router was created successfully
            assert isinstance(router, APIRouter)
            assert router.prefix == "/auth"
            
        finally:
            # Always restore original handler and cancel alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def test_create_auth_routes_with_custom_params(self):
        """Test create_auth_routes with custom parameters."""
        def timeout_handler(signum, frame):
            pytest.fail("create_auth_routes() with custom params hung")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        
        try:
            auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
            router = auth.create_auth_routes(
                prefix="/custom",
                tags=["test"],
                login_redirect_uri="http://localhost/callback"
            )
            
            assert isinstance(router, APIRouter)
            assert router.prefix == "/custom"
            
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def test_route_handlers_can_be_added_to_app(self):
        """Test that the router can be successfully added to a FastAPI app."""
        def timeout_handler(signum, frame):
            pytest.fail("Adding router to FastAPI app hung")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)  # Longer timeout for app integration
        
        try:
            app = FastAPI()
            auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
            router = auth.create_auth_routes()
            
            # This is where the hanging might occur in real usage
            app.include_router(router)
            
            # Verify routes were added
            routes = [route.path for route in app.routes]
            assert "/auth/login" in routes
            assert "/auth/logout" in routes
            assert "/auth/me" in routes
            assert "/auth/status" in routes
            
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    @patch('auth_gateway_sdk.integrations.fastapi.AuthGatewayClient')
    def test_individual_route_creation(self, mock_client_class):
        """Test individual aspects of route creation to isolate hanging point."""
        # Mock the client to avoid network calls
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        def timeout_handler(signum, frame):
            pytest.fail("Individual route creation hung")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        
        try:
            auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
            
            # Test that we can create an empty router
            router = APIRouter(prefix="/auth", tags=["authentication"])
            assert isinstance(router, APIRouter)
            
            # Test that we can get dependency functions
            get_user = auth.get_current_user()
            assert callable(get_user)
            
            get_user_optional = auth.get_current_user_optional()
            assert callable(get_user_optional)
            
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


class TestDependencyFunctions:
    """Test the dependency functions work correctly."""
    
    @patch('auth_gateway_sdk.integrations.fastapi.AuthGatewayClient')
    def test_get_current_user_dependency_creation(self, mock_client_class):
        """Test that dependency functions can be created without issues."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
        
        # Test creating dependency functions
        required_dep = auth.get_current_user()
        optional_dep = auth.get_current_user_optional()
        
        assert callable(required_dep)
        assert callable(optional_dep)
        
        # Verify they're different functions
        assert required_dep != optional_dep


class TestRouterIntegrationRealistic:
    """Test realistic integration scenarios that might cause hanging."""
    
    @patch('auth_gateway_sdk.integrations.fastapi.AuthGatewayClient')
    def test_full_integration_with_mocked_client(self, mock_client_class):
        """Test full integration with mocked client to avoid network issues."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        def timeout_handler(signum, frame):
            pytest.fail("Full integration test hung")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)
        
        try:
            # Create FastAPI app
            app = FastAPI()
            
            # Create auth integration
            auth = AuthGatewayFastAPI("https://auth-gateway-test.com")
            
            # Create and include router - this is where hanging occurs
            router = auth.create_auth_routes()
            app.include_router(router)
            
            # Create test client
            client = TestClient(app)
            
            # Verify we can access the routes (they should exist)
            # Note: We're not testing the actual functionality here,
            # just that the routes can be created and registered
            assert any("/auth/login" in str(route.path) for route in app.routes)
            
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
