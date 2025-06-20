"""
Tests for health check routes.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthRoutes:
    """Test cases for health check routes."""
    
    def test_root_health_check(self):
        """Test root health check endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Auth Gateway"
        assert data["version"] == "1.0.0"
    
    def test_explicit_health_check(self):
        """Test explicit health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Auth Gateway"
        assert data["version"] == "1.0.0"
    
    def test_ping_endpoint(self):
        """Test ping endpoint for load balancers."""
        response = client.get("/ping")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_health_endpoints_response_format(self):
        """Test that health endpoints return proper response format."""
        endpoints = ["/", "/health"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields
            assert "status" in data
            assert "service" in data
            assert "version" in data
            
            # Check field types
            assert isinstance(data["status"], str)
            assert isinstance(data["service"], str)
            assert isinstance(data["version"], str)
    
    def test_health_endpoints_headers(self):
        """Test that health endpoints return proper headers."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
