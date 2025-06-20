# Firebase Auth Gateway

A reusable authentication module based on Firebase/Google Sign-In with a stateless JWT approach.  Useful when you have multiple applications that need to authenticate users via Firebase without having to implement authentication logic and deal with Firebase and Google client configurations directly in each application.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Backend Service](#backend-service)
  - [Frontend SDK](#frontend-sdk)
- [Python Integration with FastAPI](#python-integration-with-fastapi)
  - [Prerequisites](#prerequisites)
  - [Basic FastAPI Integration](#basic-fastapi-integration)
  - [Key Differences from Standard OAuth](#key-differences-from-standard-oauth)
- [Real-Life Example: E-Commerce API with Auth Gateway](#real-life-example-e-commerce-api-with-auth-gateway)
  - [Scenario](#scenario)
  - [Authentication Patterns](#authentication-patterns)
  - [Frontend Integration](#frontend-integration)
  - [Key Benefits](#key-benefits)
- [Documentation](#documentation)
- [Prerequisites](#prerequisites-1)
- [Development](#development)
- [Building the Frontend SDK](#building-the-frontend-sdk)
- [Deployment](#deployment)

## Overview

This project provides a standardized way for applications to authenticate users via Google Sign-In. It consists of two main components:

1. **Backend Service**: A FastAPI-based service that acts as a proxy to handle Google authentication, verifies Firebase ID tokens, and enforces domain restrictions.
2. **Frontend SDK**: A React SDK that provides seamless authentication integration for client applications.

## Features

- Google Sign-In integration via Firebase
- Server-side authentication flow (no Firebase SDK required in client)
- Stateless JWT-based authentication
- Domain restriction enforcement
- Minimal code integration for client applications
- TypeScript support
- Support for both React and vanilla JavaScript
- React Context API for React applications
- Event-based API for vanilla JavaScript applications

## Project Structure

```
auth-gateway/
├── backend/             # Backend service (FastAPI)
│   ├── app/             # Application code
│   ├── tests/           # Tests
│   ├── requirements.txt # Python dependencies
│   └── README.md        # Backend documentation
├── javascript-sdk/      # JavaScript/TypeScript SDK (React)
│   ├── src/             # Source code
│   ├── dist/            # Built package
│   ├── package.json     # npm package configuration
│   └── README.md        # JavaScript SDK documentation
├── python-sdk/          # Python SDK with FastAPI integration
│   ├── auth_gateway_sdk/ # SDK source code
│   ├── tests/           # Tests
│   ├── pyproject.toml   # Python package configuration
│   └── README.md        # Python SDK documentation
├── examples/            # Integration examples
│   ├── react-client/    # React example using JavaScript SDK
│   ├── python-fastapi/  # FastAPI example using Python SDK
│   └── vanilla-js/      # Vanilla JavaScript example
└── memory-bank/         # Project documentation
```

## Quick Start

### Backend Service

1. Set up the backend service:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables include:
- `FIREBASE_API_KEY`: Your Firebase API key
- `FIREBASE_AUTH_DOMAIN`: Your Firebase auth domain
- `GOOGLE_CLIENT_ID`: Your Google Client ID
- `GOOGLE_CLIENT_SECRET`: Your Google Client Secret (required for server-side code exchange)

3. Run the service:

```bash
uvicorn app.main:app --reload
```

The service will be available at http://localhost:8000

### Frontend SDK

1. Install the SDK in your client application:

```bash
# Install from git repository (latest stable)
npm install git+https://github.com/0nri/firebase-auth-gateway.git#subdirectory=javascript-sdk

# Install specific version using git tag
npm install git+https://github.com/0nri/firebase-auth-gateway.git@v1.0.0#subdirectory=javascript-sdk
```

2. Wrap your application with the AuthProvider:

```jsx
import React from 'react';
import { AuthProvider } from 'firebase-auth-gateway-sdk';

// Auth Gateway backend URL
const authBackendUrl = "https://your-auth-gateway-backend.com";

function App() {
  return (
    <AuthProvider authBackendUrl={authBackendUrl}>
      <YourApp />
    </AuthProvider>
  );
}
```

Note: The Firebase configuration is now handled entirely by the backend service, so you don't need to provide it in the client application.

3. Use the authentication hook in your components:

```jsx
import React from 'react';
import { useAuth } from 'auth-gateway-sdk';

function LoginButton() {
  const { user, isLoading, error, login, logout } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (user) {
    return (
      <div>
        <p>Welcome, {user.display_name || user.email}!</p>
        <button onClick={logout}>Sign Out</button>
      </div>
    );
  }

  return (
    <div>
      <button onClick={login}>Sign In with Google</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}
```

## Python Integration with FastAPI

The Auth Gateway provides two ways to integrate with Python applications:

1. **Python SDK** (Recommended) - Full-featured SDK with type safety and FastAPI integration
2. **Manual HTTP API** - Direct HTTP calls for custom implementations

### Option 1: Python SDK (Recommended)

#### Installation

```bash
# Install Python SDK with FastAPI integration
pip install "git+https://github.com/0nri/firebase-auth-gateway.git#subdirectory=python-sdk[fastapi]"
```

#### Simple Integration

```python
from fastapi import FastAPI, Depends
from auth_gateway_sdk import UserData
from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI

app = FastAPI()

# One-line setup
auth = AuthGatewayFastAPI("https://your-auth-gateway.com")
app.include_router(auth.create_auth_routes())

@app.get("/")
async def public_route():
    return {"message": "Public access"}

@app.get("/protected")
async def protected_route(user: UserData = Depends(auth.require_user())):
    return {"message": f"Hello {user.email}!", "user": user}

@app.get("/optional-auth")
async def optional_auth(user: UserData = Depends(auth.get_current_user_optional())):
    return {"authenticated": user is not None, "user": user}
```

#### Benefits of Python SDK
- **Type Safety**: Full Pydantic models with IDE autocompletion
- **80% Less Code**: Minimal boilerplate compared to manual integration
- **Error Handling**: Structured exceptions (`TokenExpiredError`, `DomainNotAllowedError`, etc.)
- **Async Support**: Native async/await with automatic retries
- **FastAPI Integration**: Automatic dependency injection and route generation

### Option 2: Manual HTTP API Integration

For custom implementations or when you prefer direct control:

#### Prerequisites

```bash
pip install fastapi uvicorn requests jinja2 python-multipart
```

#### Basic Manual Integration

```python
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
from typing import Optional

# Initialize FastAPI app
app = FastAPI(title="FastAPI Auth Gateway Client")
templates = Jinja2Templates(directory="templates")

# Auth Gateway configuration
AUTH_GATEWAY_URL = "http://localhost:8000"  # Replace with your Auth Gateway URL
REDIRECT_URI = "http://localhost:8001/auth/callback"  # Your application's callback URL

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Models
class User(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None

# Auth Gateway client class
class AuthGatewayClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def generate_login_url(self, redirect_uri: str) -> str:
        """Generate a login URL from the Auth Gateway."""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"redirect_uri": redirect_uri}
        )
        response.raise_for_status()
        return response.json()["url"]
    
    def verify_token(self, token: str) -> User:
        """Verify a token with the Auth Gateway."""
        response = requests.post(
            f"{self.base_url}/verify-token",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return User(**response.json())

# Initialize Auth Gateway client
auth_client = AuthGatewayClient(AUTH_GATEWAY_URL)

# Dependency to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[User]:
    if not token:
        return None
    
    try:
        user = auth_client.verify_token(token)
        return user
    except Exception as e:
        return None

# Routes
@app.get("/")
async def root(request: Request, user: Optional[User] = Depends(get_current_user)):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "user": user}
    )

@app.get("/login")
async def login():
    """Generate a login URL and redirect the user."""
    try:
        login_url = auth_client.generate_login_url(REDIRECT_URI)
        return RedirectResponse(login_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate login URL: {str(e)}")

@app.get("/auth/callback")
async def auth_callback(token: str, response: Response):
    """
    Handle the authentication callback from the Auth Gateway.
    The gateway redirects here with the final Firebase token after successful login.
    """
    try:
        # Store the token securely in an HTTP-only cookie
        response = RedirectResponse(url="/")
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/protected")
async def protected_route(request: Request, user: User = Depends(get_current_user)):
    """A protected route that requires authentication."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return templates.TemplateResponse(
        "protected.html", 
        {"request": request, "user": user}
    )

@app.get("/logout")
async def logout(response: Response):
    """Log the user out by clearing the token cookie."""
    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    return response

# Middleware to extract token from cookies
@app.middleware("http")
async def token_middleware(request: Request, call_next):
    """Extract token from cookies and add it to request state."""
    token = request.cookies.get("access_token")
    if token:
        # Make token available to the OAuth2 scheme
        request.scope["authorization"] = f"Bearer {token}"
    
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
```

### Key Differences from Standard OAuth

The Auth Gateway simplifies the OAuth flow:

1. **No code exchange needed**: The gateway handles the complete OAuth flow and returns the final Firebase token directly
2. **Simplified callback**: Your callback receives the `token` parameter instead of handling code exchange
3. **Centralized configuration**: All Firebase and Google OAuth configuration is handled by the gateway

### Migration from Manual to Python SDK

If you have existing manual HTTP API integration, migration to the Python SDK is straightforward:

**Before (Manual - ~150 lines):**
```python
class AuthGatewayClient:
    def verify_token(self, token: str):
        response = requests.post(f"{self.base_url}/verify-token", 
                               headers={"Authorization": f"Bearer {token}"})
        # Manual error handling...
        return response.json()

async def get_current_user(token = Depends(oauth2_scheme)):
    # Custom dependency logic...
```

**After (SDK - ~30 lines):**
```python
from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI

auth = AuthGatewayFastAPI("https://your-auth-gateway.com")
app.include_router(auth.create_auth_routes())

@app.get("/protected")
async def protected(user: UserData = Depends(auth.require_user())):
    return {"user": user.email}
```

See the [Migration Guide](MIGRATION.md) for detailed migration instructions.

## Real-Life Example: E-Commerce API with Auth Gateway

Here's how to use the Auth Gateway to secure an e-commerce API service with three levels of access control.

### Scenario

**TechShop API** - An e-commerce backend service that needs to:
- Allow public access to product listings
- Require authentication for placing orders
- Restrict admin functions to company employees only

### Authentication Patterns

#### 1. Setup Auth Gateway Client & Dependencies

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import requests

# Auth Gateway configuration
AUTH_GATEWAY_URL = "https://your-auth-gateway.com"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

class AuthGatewayClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def verify_token(self, token: str) -> dict:
        response = requests.post(
            f"{self.base_url}/verify-token",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()

auth_client = AuthGatewayClient(AUTH_GATEWAY_URL)

# Authentication dependencies
async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    try:
        return auth_client.verify_token(token)
    except Exception:
        return None

async def require_authentication(user = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_admin(user = Depends(require_authentication)):
    if not user.get("email", "").endswith("@techshop.com"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

#### 2. Public Endpoint (No Authentication)

```python
@app.get("/api/products")
async def get_products():
    """Public endpoint - anyone can access product listings."""
    return [
        {"id": "1", "name": "Laptop Pro", "price": 1299.99},
        {"id": "2", "name": "Wireless Mouse", "price": 29.99}
    ]
```

#### 3. Authenticated Endpoint (Login Required)

```python
@app.post("/api/orders")
async def create_order(order_data: dict, user = Depends(require_authentication)):
    """Authenticated endpoint - requires valid user token."""
    return {
        "order_id": "order_123",
        "user_email": user["email"],
        "status": "created",
        "message": f"Order created for {user['display_name'] or user['email']}"
    }
```

#### 4. Admin Endpoint (Role-Based Access)

```python
@app.get("/api/admin/analytics")
async def get_analytics(admin = Depends(require_admin)):
    """Admin endpoint - requires company employee email domain."""
    return {
        "total_revenue": 15000.50,
        "total_orders": 42,
        "admin_user": admin["email"]
    }
```

### Frontend Integration

#### Protected Route Component

```jsx
// components/ProtectedRoute.jsx
import React from 'react';
import { useAuth } from 'firebase-auth-gateway-sdk';

function ProtectedRoute({ children, requireAdmin = false }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div>Loading...</div>;
  
  if (!user) {
    // Redirect to login or show login component
    return <LoginPage />;
  }

  if (requireAdmin && !user.email.endsWith('@techshop.com')) {
    return <div>Access Denied: Admin privileges required</div>;
  }

  return children;
}

// Usage in routes
<Route path="/orders" element={
  <ProtectedRoute>
    <OrdersPage />
  </ProtectedRoute>
} />

<Route path="/admin" element={
  <ProtectedRoute requireAdmin>
    <AdminPage />
  </ProtectedRoute>
} />
```

#### Making Authenticated API Calls

```jsx
// Making API calls with authentication
const { user } = useAuth();
const token = localStorage.getItem('auth_token');

// Call authenticated endpoint
const response = await fetch('/api/orders', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(orderData)
});
```

### Authentication Flow

1. **User visits website** → Can browse products (public)
2. **User tries to order** → Redirected to Auth Gateway login
3. **User signs in with Google** → Receives token, can place orders
4. **Employee accesses admin** → Additional domain check for admin features

### Security Features

- **Public Access**: Product browsing without authentication
- **Token Validation**: Every protected API call verifies token with Auth Gateway  
- **Role-Based Access**: Admin endpoints check user email domain
- **Automatic Redirects**: Frontend redirects unauthenticated users to login

### Key Benefits

1. **Centralized Authentication**: Single Auth Gateway serves multiple services
2. **Domain Restrictions**: Automatic filtering of users by email domain
3. **Stateless Design**: No session state to manage in the API service
4. **Frontend Integration**: Seamless user experience with automatic token handling
5. **Role-Based Security**: Fine-grained access control based on user attributes

## Documentation

- [Backend Service Documentation](backend/README.md) 
- [JavaScript SDK Documentation](javascript-sdk/README.md)
- [Python SDK Documentation](python-sdk/README.md)
- [Migration Guide](MIGRATION.md)
- [Project Design Document](authModuleDesign.md)

## Examples

- [React Client Example](examples/react-client/README.md) - JavaScript SDK integration
- [FastAPI Example](examples/python-fastapi/README.md) - Python SDK integration  
- [Vanilla JavaScript Example](examples/vanilla-js/README.md) - Basic JavaScript integration

## Prerequisites

### Backend Service

- Python 3.10+
- Firebase project with Google Sign-In enabled
- Google Cloud project with OAuth 2.0 Client ID and Secret
- Google Cloud service account with Firebase Admin SDK permissions

### Frontend SDK

- React 17+ application (for React integration)
- Modern browser with localStorage support

## Development

### Backend Service

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### JavaScript SDK

```bash
cd javascript-sdk
npm install
npm run dev
```

### Python SDK

```bash
cd python-sdk
pip install -e ".[dev]"
pytest
```

## Building the SDKs

### JavaScript SDK

```bash
cd javascript-sdk
npm run build
```

### Python SDK

```bash
cd python-sdk
python -m build
```

## Deployment

### Backend Service

The backend service is designed to be deployed to Google Cloud Run:

```bash
cd backend
gcloud run deploy auth-gateway-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="FIREBASE_PROJECT_ID=your-project-id,FIREBASE_API_KEY=your-api-key,FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com,GOOGLE_CLIENT_ID=your-client-id,ALLOWED_EMAIL_DOMAIN_REGEX=^.+@yourdomain\.com$,CORS_ALLOWED_ORIGINS=https://your-app.com"
```

For sensitive environment variables like `GOOGLE_CLIENT_SECRET`, use Secret Manager:

```bash
# First, create the secret
gcloud secrets create auth-gateway-google-client-secret --replication-policy="automatic"
echo -n "your-client-secret" | gcloud secrets versions add auth-gateway-google-client-secret --data-file=-

# Then reference it in your deployment
gcloud run deploy auth-gateway-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="FIREBASE_PROJECT_ID=your-project-id,..." \
  --set-secrets="GOOGLE_CLIENT_SECRET=auth-gateway-google-client-secret:latest"
```

### JavaScript SDK

Publish using git-based distribution:

```bash
# JavaScript SDK is distributed via git subdirectory
npm install git+https://github.com/0nri/firebase-auth-gateway.git#subdirectory=javascript-sdk
```

### Python SDK  

Publish using git-based distribution:

```bash
# Python SDK is distributed via git subdirectory
pip install git+https://github.com/0nri/firebase-auth-gateway.git#subdirectory=python-sdk
```

For more deployment options, see the [Migration Guide](MIGRATION.md).
