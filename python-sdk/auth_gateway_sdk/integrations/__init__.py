"""
Integration modules for various frameworks.
"""
from .fastapi import AuthGatewayFastAPI, create_auth_dependency, get_auth_client, setup_auth_middleware

__all__ = [
    "AuthGatewayFastAPI", 
    "create_auth_dependency", 
    "get_auth_client", 
    "setup_auth_middleware"
]
