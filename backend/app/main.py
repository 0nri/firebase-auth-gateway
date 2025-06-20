"""
Main FastAPI application for Auth Gateway.

This is the new modular version that replaces the monolithic main.py.
All business logic has been moved to services, routes, and models.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings, setup_logging, Settings
from .routes import auth_router, health_router
from .models.responses import UserData

# Initialize settings and logging
settings = get_settings()
setup_logging(settings)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting Auth Gateway in {settings.environment} mode")
    logger.info(f"CORS origins configured: {len(settings.get_cors_origins())} origins")
    logger.info(f"Domain restriction active: {settings.allowed_email_domain_regex != '.*'}")
    
    yield
    
    # Shutdown
    logger.info("Auth Gateway shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="Auth Gateway",
    description="A reusable authentication service for internal applications",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None
)

# Configure CORS
cors_origins = settings.get_cors_origins()
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS configured with {len(cors_origins)} allowed origins")
else:
    logger.warning("No CORS origins configured - this may cause issues in production")

# Include routers
app.include_router(health_router)
app.include_router(auth_router)

# Add token verification endpoint at root level
@app.post("/verify-token", response_model=UserData, tags=["authentication"])
async def verify_id_token(
    authorization: str = Header(None),
    settings: Settings = Depends(get_settings)
):
    """Verify a Firebase ID token and return user data if valid."""
    from .services import TokenService, DomainService
    
    try:
        # Extract token from header
        token_service = TokenService()
        token = token_service.extract_token_from_header(authorization)
        
        # Verify token and extract claims
        decoded_token = token_service.verify_token(token)
        token_service.validate_token_claims(decoded_token)
        
        # Extract user data
        user_data_dict = token_service.extract_user_data(decoded_token)
        email = user_data_dict.get("email", "")
        
        # Validate email domain
        domain_service = DomainService(settings)
        domain_service.validate_and_raise(email)
        
        logger.debug("Token verification completed successfully")
        return UserData(**user_data_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {type(e).__name__}")
        raise HTTPException(status_code=401, detail="Token verification failed")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}")
    
    # Don't expose internal errors in production
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An internal error occurred"
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": f"Internal error: {type(exc).__name__}"
            }
        )


# Health check for load balancers (duplicate of /health but at root level)
@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancer health checks."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
