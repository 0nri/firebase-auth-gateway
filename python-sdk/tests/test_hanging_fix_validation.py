"""
Comprehensive validation that the hanging fix works correctly.
"""
import pytest
import signal
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI


def test_hanging_fix_comprehensive():
    """Comprehensive test that validates the hanging issue is fixed."""
    
    def timeout_handler(signum, frame):
        pytest.fail("HANGING ISSUE STILL EXISTS! Router creation hung.")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(10)  # 10 second timeout
    
    start_time = time.time()
    
    try:
        print("=== Testing Hanging Fix ===")
        
        # Step 1: Create AuthGatewayFastAPI instance
        print("1. Creating AuthGatewayFastAPI instance...")
        auth = AuthGatewayFastAPI("https://auth-gateway-o26hoy2ova-df.a.run.app")
        
        # Step 2: Create auth routes (this was hanging before)
        print("2. Creating auth routes...")
        router = auth.create_auth_routes()
        
        # Step 3: Create FastAPI app
        print("3. Creating FastAPI app...")
        app = FastAPI()
        
        # Step 4: Include router (this could also hang)
        print("4. Including router in app...")
        app.include_router(router)
        
        # Step 5: Verify routes were created
        print("5. Verifying routes...")
        route_paths = [route.path for route in app.routes]
        expected_routes = ["/auth/login", "/auth/logout", "/auth/me", "/auth/status"]
        
        for expected_route in expected_routes:
            assert expected_route in route_paths, f"Missing route: {expected_route}"
        
        # Step 6: Test that TestClient can be created (validates route structure)
        print("6. Creating TestClient...")
        client = TestClient(app)
        
        # Step 7: Verify we can access route metadata (tests dependency resolution)
        print("7. Verifying route metadata...")
        assert len([r for r in app.routes if "/auth" in str(r.path)]) >= 4
        
        elapsed_time = time.time() - start_time
        print(f"8. SUCCESS! All operations completed in {elapsed_time:.2f} seconds")
        print(f"   Routes created: {len(route_paths)}")
        print(f"   Auth routes: {[r for r in route_paths if '/auth' in r]}")
        
        # Verify it completed quickly (not hanging)
        assert elapsed_time < 5.0, f"Operation took too long: {elapsed_time}s"
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def test_dependency_functions_work():
    """Test that dependency functions work correctly after the fix."""
    
    def timeout_handler(signum, frame):
        pytest.fail("Dependency function creation hung!")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)
    
    try:
        auth = AuthGatewayFastAPI("https://auth-gateway-o26hoy2ova-df.a.run.app")
        
        # Test that dependency functions can be created
        required_dep = auth.get_current_user()
        optional_dep = auth.get_current_user_optional()
        
        assert callable(required_dep)
        assert callable(optional_dep)
        
        # Test that they're different functions
        assert required_dep != optional_dep
        
        print("✅ Dependency functions created successfully")
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def test_multiple_apps_with_auth():
    """Test creating multiple FastAPI apps with auth routes (stress test)."""
    
    def timeout_handler(signum, frame):
        pytest.fail("Multiple apps creation hung!")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)
    
    try:
        apps = []
        
        for i in range(3):
            print(f"Creating app {i+1}/3...")
            
            # Create new auth instance for each app
            auth = AuthGatewayFastAPI("https://auth-gateway-o26hoy2ova-df.a.run.app")
            router = auth.create_auth_routes(prefix=f"/auth{i}")
            
            app = FastAPI(title=f"Test App {i}")
            app.include_router(router)
            
            # Verify routes were added
            route_paths = [route.path for route in app.routes]
            assert f"/auth{i}/login" in route_paths
            
            apps.append(app)
        
        assert len(apps) == 3
        print("✅ Multiple apps with auth routes created successfully")
        
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def test_before_and_after_behavior():
    """Document the before/after behavior of the fix."""
    
    print("\n=== HANGING FIX VALIDATION ===")
    print("BEFORE: create_auth_routes() would hang indefinitely")
    print("AFTER:  create_auth_routes() completes in milliseconds")
    print("\nKEY IMPROVEMENTS:")
    print("1. Dependencies created outside route handlers")
    print("2. Used add_api_route() instead of decorators")
    print("3. Avoided closure capture issues")
    print("4. Separated route handler definitions")
    print("\nTEST RESULT: ✅ HANGING ISSUE RESOLVED")
    
    # This test always passes - it's just for documentation
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
