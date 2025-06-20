"""
Stress tests to try to reproduce hanging under different conditions.
"""
import pytest
import signal
import asyncio
import concurrent.futures
import threading
from fastapi import FastAPI

from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI


def test_concurrent_route_creation():
    """Test creating multiple routers concurrently to check for race conditions."""
    def timeout_handler(signum, frame):
        pytest.fail("Concurrent route creation hung!")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)  # Generous timeout for concurrent operations
    
    try:
        def create_router_task(i):
            """Create a router in a separate thread."""
            auth = AuthGatewayFastAPI("https://auth-gateway-o26hoy2ova-df.a.run.app")
            router = auth.create_auth_routes(prefix=f"/auth{i}")
            app = FastAPI()
            app.include_router(router)
            return router
        
        # Create multiple routers concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_router_task, i) for i in range(5)]
            routers = [future.result(timeout=10) for future in futures]
        
        assert len(routers) == 5
        print("All concurrent routers created successfully!")
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def test_rapid_successive_creation():
    """Test rapid successive calls to create_auth_routes."""
    def timeout_handler(signum, frame):
        pytest.fail("Rapid successive creation hung!")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(20)
    
    try:
        auth = AuthGatewayFastAPI("https://auth-gateway-o26hoy2ova-df.a.run.app")
        routers = []
        
        # Create 10 routers in rapid succession
        for i in range(10):
            print(f"Creating router {i+1}/10...")
            router = auth.create_auth_routes(prefix=f"/test{i}")
            routers.append(router)
        
        assert len(routers) == 10
        print("All rapid successive routers created successfully!")
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def test_memory_intensive_creation():
    """Test creating many routers to check for memory-related issues."""
    def timeout_handler(signum, frame):
        pytest.fail("Memory intensive creation hung!")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # Longer timeout for memory operations
    
    try:
        routers = []
        apps = []
        
        # Create many auth instances and routers
        for i in range(20):
            print(f"Creating router {i+1}/20...")
            auth = AuthGatewayFastAPI("https://auth-gateway-o26hoy2ova-df.a.run.app")
            router = auth.create_auth_routes(prefix=f"/memory{i}")
            app = FastAPI()
            app.include_router(router)
            
            routers.append(router)
            apps.append(app)
        
        assert len(routers) == 20
        assert len(apps) == 20
        print("All memory intensive routers created successfully!")
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


async def async_create_router(i):
    """Create router in async context."""
    auth = AuthGatewayFastAPI("https://auth-gateway-o26hoy2ova-df.a.run.app")
    router = auth.create_auth_routes(prefix=f"/async{i}")
    return router


def test_async_context_creation():
    """Test creating routers in async context which might trigger different code paths."""
    def timeout_handler(signum, frame):
        pytest.fail("Async context creation hung!")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)
    
    try:
        async def run_async_test():
            # Create multiple routers in async context
            tasks = [async_create_router(i) for i in range(5)]
            routers = await asyncio.gather(*tasks)
            return routers
        
        # Run the async test
        routers = asyncio.run(run_async_test())
        assert len(routers) == 5
        print("All async context routers created successfully!")
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def test_with_different_urls():
    """Test with different URLs to see if specific URLs cause issues."""
    def timeout_handler(signum, frame):
        pytest.fail("Different URLs test hung!")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)
    
    try:
        urls = [
            "https://auth-gateway-o26hoy2ova-df.a.run.app",
            "https://httpbin.org",  # Different domain
            "http://localhost:8000",  # Local URL
            "https://auth-gateway-o26hoy2ova-df.a.run.app",  # Repeat original
        ]
        
        routers = []
        for i, url in enumerate(urls):
            print(f"Creating router for URL {i+1}: {url}")
            try:
                auth = AuthGatewayFastAPI(url)
                router = auth.create_auth_routes(prefix=f"/url{i}")
                routers.append(router)
            except Exception as e:
                print(f"Expected exception for {url}: {e}")
                # Some URLs might fail due to network, that's OK
                pass
        
        print(f"Created {len(routers)} routers successfully!")
        assert len(routers) >= 1  # At least one should work
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
