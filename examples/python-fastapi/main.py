"""
FastAPI Auth Gateway Client Example - Updated with Python SDK

This example demonstrates how to integrate the Auth Gateway Python SDK
with a FastAPI application, showing the dramatic reduction in boilerplate code.
"""
from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

# Import the Auth Gateway SDK
from auth_gateway_sdk import UserData
from auth_gateway_sdk.integrations.fastapi import AuthGatewayFastAPI

# Initialize FastAPI app
app = FastAPI(title="FastAPI Auth Gateway Client (SDK Example)")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Auth Gateway configuration
AUTH_GATEWAY_URL = "http://localhost:8000"  # Replace with your Auth Gateway URL
CALLBACK_URI = "http://localhost:8001/auth/callback"  # Your application's callback URL

# Initialize Auth Gateway SDK with FastAPI integration
auth = AuthGatewayFastAPI(AUTH_GATEWAY_URL)

# Add authentication routes (login, logout, me, status)
app.include_router(auth.create_auth_routes())

# Custom callback handler that sets cookies and redirects
@app.get("/auth/callback")
async def auth_callback(token: str):
    """
    Handle the authentication callback from the Auth Gateway.
    The gateway redirects here with the final Firebase token after successful login.
    """
    try:
        # Verify the token is valid
        user = await auth.client.verify_token(token)
        
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
        # In a real application, you might want to redirect to an error page
        return RedirectResponse(url="/?error=auth_failed")

# Routes using the SDK dependencies
@app.get("/")
async def home(
    request: Request, 
    user: UserData = Depends(auth.get_current_user_optional())
):
    """Home page - shows login status."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "auth_url": f"{AUTH_GATEWAY_URL}/auth/login?redirect_uri={CALLBACK_URI}"
        }
    )

@app.get("/protected")
async def protected_route(
    request: Request,
    user: UserData = Depends(auth.require_user())
):
    """A protected route that requires authentication."""
    return templates.TemplateResponse(
        "protected.html",
        {
            "request": request,
            "user": user
        }
    )

@app.get("/profile")
async def profile(user: UserData = Depends(auth.require_user())):
    """API endpoint that returns user profile as JSON."""
    return {
        "uid": user.uid,
        "email": user.email,
        "display_name": user.display_name,
        "photo_url": user.photo_url
    }

@app.get("/optional-auth")
async def optional_auth_example(user: UserData = Depends(auth.get_current_user_optional())):
    """Example of optional authentication."""
    if user:
        return {
            "authenticated": True,
            "message": f"Hello {user.email}!",
            "user": user
        }
    else:
        return {
            "authenticated": False,
            "message": "Hello anonymous user!"
        }

# Manual login route that generates the URL
@app.get("/login")
async def manual_login():
    """Manual login route that generates and redirects to Google OAuth URL."""
    try:
        login_response = await auth.generate_login_url(CALLBACK_URI)
        return RedirectResponse(url=login_response.url)
    except Exception:
        return RedirectResponse(url="/?error=login_failed")

# Custom logout that clears cookies
@app.get("/logout")
async def logout():
    """Log the user out by clearing the token cookie."""
    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    return response

# Health check that also tests Auth Gateway connectivity
@app.get("/health")
async def health_check():
    """Health check that includes Auth Gateway status."""
    try:
        gateway_health = await auth.client.health_check()
        return {
            "status": "healthy",
            "auth_gateway": {
                "status": gateway_health.status,
                "service": gateway_health.service
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "auth_gateway": {
                "status": "error",
                "error": str(e)
            }
        }

# Middleware to extract token from cookies for Bearer token dependencies
@app.middleware("http")
async def token_middleware(request: Request, call_next):
    """Extract token from cookies and add to request headers."""
    token = request.cookies.get("access_token")
    if token and "authorization" not in request.headers:
        # Create mutable headers
        headers = dict(request.headers)
        headers["authorization"] = f"Bearer {token}"
        
        # Update request scope
        request.scope["headers"] = [
            (k.encode(), v.encode()) for k, v in headers.items()
        ]
    
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
