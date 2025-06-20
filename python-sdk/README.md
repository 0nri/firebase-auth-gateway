# Auth Gateway Python SDK

A Python SDK for integrating with the Auth Gateway service, providing Firebase authentication with Google Sign-In.

## Installation

Install directly from git repository:

```bash
# Install latest version
pip install "git+https://github.com/0nri/firebase-auth-gateway.git#subdirectory=python-sdk&egg=auth-gateway-sdk"

# Install specific version
pip install "git+https://github.com/0nri/firebase-auth-gateway.git@v1.0.0#subdirectory=python-sdk&egg=auth-gateway-sdk"

# Install with FastAPI integration
pip install "git+https://github.com/0nri/firebase-auth-gateway.git#subdirectory=python-sdk&egg=auth-gateway-sdk[fastapi]"
```

## Quick Start

### Basic Usage

```python
import asyncio
from auth_gateway_sdk import AuthGatewayClient

async def main():
    # Initialize client
    client = AuthGatewayClient("https://your-auth-gateway.com")
    
    # Generate login URL
    login_response = await client.generate_login_url("https://myapp.com/callback")
    print(f"Login URL: {login_response.url}")
    
    # Verify a token (from your auth callback)
    user = await client.verify_token("firebase-id-token")
    print(f"User: {user.email}")
    
    # Check service health
    health = await client.health_check()
    print(f"Service status: {health.status}")
    
    await client.close()

# Run async function
asyncio.run(main())
```

### Synchronous Usage

```python
from auth_gateway_sdk import SyncAuthGatewayClient

# Initialize sync client
client = SyncAuthGatewayClient("https://your-auth-gateway.com")

# Generate login URL
login_response = client.generate_login_url("https://myapp.com/callback")
print(f"Login URL: {login_response.url}")

# Verify token
user = client.verify_token("firebase-id-token")
print(f"User: {user.email}")

client.close()
```

## FastAPI Integration

The SDK provides excellent FastAPI integration with dependency injection, middleware, and route helpers.

### Simple FastAPI Integration

```python
from fastapi import FastAPI, Depends
from auth_gateway_sdk import UserData
from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI

app = FastAPI()

# Initialize auth integration
auth = AuthGatewayFastAPI("https://your-auth-gateway.com")

# Add authentication routes
app.include_router(auth.create_auth_routes())

@app.get("/")
async def public_route():
    return {"message": "This is a public route"}

@app.get("/profile")
async def protected_route(user: UserData = Depends(auth.require_user())):
    return {"message": f"Hello {user.email}!", "user": user}

@app.get("/optional-auth")
async def optional_auth_route(user: UserData = Depends(auth.get_current_user_optional())):
    if user:
        return {"message": f"Hello {user.email}!", "authenticated": True}
    else:
        return {"message": "Hello anonymous!", "authenticated": False}
```

### Manual Dependency Setup

```python
from fastapi import FastAPI, Depends
from auth_gateway_sdk import AuthGatewayClient, UserData
from auth_gateway_sdk.integrations.fastapi import create_auth_dependency

app = FastAPI()
client = AuthGatewayClient("https://your-auth-gateway.com")

# Create authentication dependency
require_auth = create_auth_dependency(client, required=True)
optional_auth = create_auth_dependency(client, required=False)

@app.get("/protected")
async def protected(user: UserData = Depends(require_auth)):
    return {"user": user.email}

@app.get("/optional")
async def optional(user: UserData = Depends(optional_auth)):
    return {"authenticated": user is not None}
```

## Configuration

### Environment Variables

```bash
# Required
AUTH_GATEWAY_URL=https://your-auth-gateway.com

# Optional
AUTH_GATEWAY_TIMEOUT=30
AUTH_GATEWAY_RETRY_ATTEMPTS=3
AUTH_GATEWAY_VERIFY_SSL=true
```

```python
from auth_gateway_sdk import AuthGatewayClient

# Use environment variables
client = AuthGatewayClient()  # Reads from AUTH_GATEWAY_URL
```

### Configuration Object

```python
from auth_gateway_sdk import AuthGatewayClient, AuthGatewayConfig

# Create configuration
config = AuthGatewayConfig(
    base_url="https://your-auth-gateway.com",
    timeout=60,
    retry_attempts=3,
    verify_ssl=True
)

client = AuthGatewayClient(config)
```

## Error Handling

The SDK provides structured exception handling:

```python
from auth_gateway_sdk import (
    AuthGatewayClient,
    AuthenticationError,
    TokenExpiredError,
    TokenInvalidError,
    DomainNotAllowedError,
    NetworkError,
    ConfigurationError
)

client = AuthGatewayClient("https://your-auth-gateway.com")

try:
    user = await client.verify_token("some-token")
    print(f"User: {user.email}")

except TokenExpiredError:
    print("Token has expired, redirect to login")

except TokenInvalidError:
    print("Token is invalid, clear stored token")

except DomainNotAllowedError:
    print("User's email domain is not allowed")

except NetworkError as e:
    print(f"Network error: {e.message}")

except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")

except ConfigurationError as e:
    print(f"SDK misconfigured: {e.message}")
```

## Models

All API responses use Pydantic models for type safety:

```python
from auth_gateway_sdk import UserData, LoginResponse, HealthResponse

# UserData model
user = UserData(
    uid="firebase-uid",
    email="user@example.com", 
    display_name="John Doe",
    photo_url="https://example.com/photo.jpg"
)

# All models have full IDE support with type hints
print(user.email)  # Type: str
print(user.display_name)  # Type: Optional[str]
```

## Advanced Usage

### Context Manager

```python
async with AuthGatewayClient("https://your-auth-gateway.com") as client:
    user = await client.verify_token("token")
    print(user.email)
# Client automatically closed
```

### Custom HTTP Configuration

```python
from auth_gateway_sdk import AuthGatewayConfig, AuthGatewayClient

config = AuthGatewayConfig(
    base_url="https://your-auth-gateway.com",
    timeout=120,  # 2 minutes
    retry_attempts=5,  # Retry failed requests 5 times
    verify_ssl=False  # Disable SSL verification (not recommended)
)

client = AuthGatewayClient(config)
```

### Logging

The SDK uses Python's standard logging module:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger("auth_gateway_sdk")
logger.setLevel(logging.INFO)
```

## Migration from HTTP API

If you're currently using direct HTTP API calls, migration is straightforward:

### Before (Manual HTTP)

```python
import requests

def verify_token(token: str):
    response = requests.post(
        f"{AUTH_GATEWAY_URL}/verify-token",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

def generate_login_url(redirect_uri: str):
    response = requests.post(
        f"{AUTH_GATEWAY_URL}/auth/login",
        json={"redirect_uri": redirect_uri}
    )
    return response.json()["url"]
```

### After (SDK)

```python
from auth_gateway_sdk import AuthGatewayClient

client = AuthGatewayClient("https://your-auth-gateway.com")

async def verify_token(token: str):
    return await client.verify_token(token)  # Returns UserData object

async def generate_login_url(redirect_uri: str):
    response = await client.generate_login_url(redirect_uri)
    return response.url
```

### Benefits of Migration

- **Type Safety**: Pydantic models with full IDE support
- **Error Handling**: Structured exceptions vs manual status code checking
- **Async Support**: Native async/await support
- **Retries**: Automatic retry logic with exponential backoff
- **Framework Integration**: FastAPI dependencies, middleware, route helpers
- **Maintenance**: Automatic model updates with backend changes

## Development

### Running Tests

```bash
cd python-sdk
pip install -e ".[dev]"
pytest
```

### Code Formatting

```bash
black auth_gateway_sdk/
isort auth_gateway_sdk/
```

### Type Checking

```bash
mypy auth_gateway_sdk/
```

## License

MIT License - see LICENSE file for details.
