"""
This file serves as an entry point for Cloud Run to find the FastAPI application.
Cloud Run looks for a module named 'main' at the root level.
"""

# Import the app from the app package
from app.main import app

# This block is executed when running locally with 'python main.py'
# In production, Cloud Run will use the imported 'app' directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080)
