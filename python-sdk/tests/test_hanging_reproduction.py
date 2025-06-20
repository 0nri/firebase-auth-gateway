"""
Test to reproduce the exact hanging issue reported by the client.
"""
import pytest
import signal
from fastapi import FastAPI

from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI


def test_reproduce_client_hanging_issue():
    """Test with the exact URL and scenario the client reported."""
    def timeout_handler(signum, frame):
        pytest.fail("Reproduced the hanging issue! create_auth_routes() hung.")
    
    # Set up timeout handler - use shorter timeout to fail fast
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(10)  # 10 second timeout
    
    try:
        print("Testing with the exact client scenario...")
        
        # Use the exact URL the client reported
        auth = AuthGatewayFastAPI("https://auth-gateway-o26hoy2ova-df.a.run.app")
        
        print("Created AuthGatewayFastAPI instance...")
        
        # This is where the client reports hanging
        print("Calling create_auth_routes()...")
        router = auth.create_auth_routes()
        
        print("create_auth_routes() completed successfully!")
        
        # Try adding to FastAPI app as well
        print("Creating FastAPI app...")
        app = FastAPI()
        
        print("Adding router to app...")
        app.include_router(router)
        
        print("Router successfully added to FastAPI app!")
        
        assert router is not None
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def test_reproduce_with_network_delays():
    """Test if network issues could cause hanging."""
    def timeout_handler(signum, frame):
        pytest.fail("Network-related hanging detected!")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)  # Longer timeout for network operations
    
    try:
        print("Testing with potential network delays...")
        
        # Use client's exact URL
        auth = AuthGatewayFastAPI("https://auth-gateway-o26hoy2ova-df.a.run.app")
        
        # Try to create multiple routers to see if it's cumulative
        print("Creating router 1...")
        router1 = auth.create_auth_routes(prefix="/auth1")
        
        print("Creating router 2...")  
        router2 = auth.create_auth_routes(prefix="/auth2")
        
        print("Both routers created successfully!")
        
        assert router1 is not None
        assert router2 is not None
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print statements
