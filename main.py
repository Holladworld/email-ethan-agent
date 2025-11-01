from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Create FastAPI application
app = FastAPI(
    title="Email Ethan API",
    description="Your AI email management assistant",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint - basic health check"""
    return {
        "message": "Email Ethan API is running!",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "email-ethan-agent",
            "timestamp": "2024-01-15T10:00:00Z"  # We'll make this dynamic later
        }
    )

@app.get("/.well-known/agent.json")
async def agent_discovery():
    """Agent discovery endpoint - Telex will look for this"""
    return {
        "name": "Email Ethan",
        "description": "AI-powered email management assistant",
        "url": "http://localhost:8000",  # We'll update this when deployed
        "version": "1.0.0",
        "provider": {
            "organization": "Holladworld",
            "url": "https://github.com/Holladworld"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes during development
    )
