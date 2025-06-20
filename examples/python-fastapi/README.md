# FastAPI Auth Gateway Example - Python SDK

This example demonstrates how to integrate the Auth Gateway Python SDK with a FastAPI application, showcasing the dramatic reduction in boilerplate code compared to manual HTTP API integration.

## Before vs After Comparison

### Before (Manual HTTP API Integration) - ~150 lines
- Manual HTTP requests with `requests` library
- Custom error handling for each status code
- Manual Pydantic model definitions
- Custom authentication dependency
- Manual middleware for cookie handling
- Verbose token verification logic

### After (Python SDK) - ~30 lines of auth code
- One-line SDK initialization: `auth = AuthGatewayFastAPI(url)`
- Automatic dependency injection: `Depends(auth.require_user())`
- Built-in error handling with structured exceptions
- Type safety with IDE autocompletion
- Automatic retry logic and connection pooling

## Installation

1. **Install the Python SDK:**
   ```bash
   # For local development (from this repository)
   pip install -e ../../python-sdk[fastapi]
   
   # For production (from git)
   pip install "git+https://github.com/0nri/firebase-auth-gateway.git#subdirectory=python-sdk&egg=auth-gateway-sdk[fastapi]"
   ```

2. **Install other dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set up your Auth Gateway URL in the example:

```python
# In main.py
AUTH_GATEWAY_URL = "http://localhost:8000"  # Your Auth Gateway URL
```

For production, you can use environment variables:

```bash
export AUTH_GATEWAY_URL=https://your-auth-gateway.com
```

## Running the Example

1. **Start the Auth Gateway backend** (if not already running):
   ```bash
   cd ../../backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start this FastAPI example:**
   ```bash
   uvicorn main:app --reload --port 8001
   ```

3. **Visit the application:**
   - Home page: http://localhost:8001
   - Protected route: http://localhost:8001/protected
   - API profile: http://localhost:8001/profile
   - Health check: http://localhost:8001/health

## Key Features Demonstrated

### 1. **Minimal Setup**
```python
from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI

# One line setup
auth = AuthGatewayFastAPI("http://localhost:8000")

# Add automatic auth routes (/auth/login, /auth/logout, /auth/me, /auth/status)
app.include_router(auth.create_auth_routes())
```

### 2. **Easy Dependencies**
```python
# Require authentication
@app.get("/protected")
async def protected(user: UserData = Depends(auth.require_user())):
    return {"user": user.email}

# Optional authentication
@app.get("/optional")
async def optional(user: UserData = Depends(auth.get_current_user_optional())):
    return {"authenticated": user is not None}
```

### 3. **Type Safety**
```python
# Full IDE support with autocompletion
def handle_user(user: UserData):
    print(user.email)        # Type: str
    print(user.display_name) # Type: Optional[str]
    print(user.uid)          # Type: str
    print(user.photo_url)    # Type: Optional[str]
```

### 4. **Structured Error Handling**
```python
from auth_gateway_sdk import TokenExpiredError, DomainNotAllowedError

try:
    user = await client.verify_token(token)
except TokenExpiredError:
    # Handle expired tokens specifically
    pass
except DomainNotAllowedError:
    # Handle domain restrictions
    pass
```

### 5. **Automatic Health Checks**
```python
@app.get("/health")
async def health_check():
    try:
        gateway_health = await auth.client.health_check()
        return {"status": "healthy", "auth_gateway": gateway_health}
    except Exception:
        return {"status": "degraded"}
```

## Code Reduction Analysis

| Aspect | Manual HTTP API | Python SDK | Reduction |
|--------|-----------------|------------|-----------|
| **Lines of code** | ~150 lines | ~30 lines | 80% less |
| **Dependencies** | Custom auth logic | `Depends(auth.require_user())` | 90% less |
| **Error handling** | Manual status codes | Structured exceptions | 70% less |
| **Type safety** | Manual models | Built-in Pydantic | 100% automatic |
| **Retries** | Manual implementation | Built-in | 100% automatic |

## Authentication Flow

1. **User visits protected route** → Redirected to login
2. **Login route** → Generates Google OAuth URL via Auth Gateway
3. **Google authentication** → User authenticates with Google
4. **Auth Gateway callback** → Receives auth code, exchanges for Firebase token
5. **Client callback** → Receives Firebase token, sets HTTP-only cookie
6. **Protected route access** → Token automatically verified via dependency

## File Structure

```
examples/python-fastapi/
├── main.py              # FastAPI app with SDK integration
├── requirements.txt     # Dependencies including SDK
├── README.md           # This file
└── templates/
    ├── index.html      # Home page template
    └── protected.html  # Protected page template
```

## Environment Variables

The SDK supports these environment variables:

```bash
# Required
AUTH_GATEWAY_URL=https://your-auth-gateway.com

# Optional
AUTH_GATEWAY_TIMEOUT=30
AUTH_GATEWAY_RETRY_ATTEMPTS=3
AUTH_GATEWAY_VERIFY_SSL=true
```

## Development

### Running with Development SDK

For local development when working on the SDK:

```bash
# Install SDK in development mode
pip install -e ../../python-sdk[fastapi]

# Run with auto-reload
uvicorn main:app --reload --port 8001
```

### Testing Authentication

1. Visit http://localhost:8001
2. Click "Login" to start authentication flow
3. Authenticate with Google
4. Return to application as authenticated user
5. Access protected routes

## Migration from Manual HTTP API

If you have an existing FastAPI application using manual HTTP API integration, see the [Migration Guide](../../MIGRATION.md#migration-http-api-integration--python-sdk-optional) for step-by-step instructions.

The migration typically involves:
1. Installing the Python SDK
2. Replacing manual HTTP client code with SDK client
3. Updating dependencies to use SDK dependency injection
4. Removing custom error handling in favor of SDK exceptions

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure the SDK is installed with FastAPI extras:
   ```bash
   pip install "../../python-sdk[fastapi]"
   ```

2. **Token Not Found**: Ensure the middleware is extracting cookies properly and the Auth Gateway callback is setting cookies correctly.

3. **CORS Issues**: Make sure your Auth Gateway backend has the correct CORS configuration for your client URL.

4. **Environment Variables**: Double-check that `AUTH_GATEWAY_URL` points to your running Auth Gateway instance.

### Debug Mode

Enable debug logging to see detailed request/response information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

- Explore the [Python SDK documentation](../../python-sdk/README.md)
- Check out the [Auth Gateway backend](../../backend/README.md)
- See the [JavaScript SDK example](../react-client/README.md)
- Review the [Migration Guide](../../MIGRATION.md)
