from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models.a2a import JSONRPCRequest
from agents.email_ethan.agent import EmailEthanAgent  # Import our specialized agent

# Get port from environment or default to 8000
PORT = int(os.getenv("PORT", 8000))

# Initialize Email Ethan
email_ethan = EmailEthanAgent()

app = FastAPI(
    title="Email Ethan API",
    description="Your AI email management assistant", 
    version="1.0.0"
)

# Add CORS middleware to handle requests from Telex
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - you can restrict this later
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Simple authentication endpoints
@app.get("/auth/gmail")
async def start_gmail_auth():
    """Start Gmail OAuth flow - simple version"""
    return {
        "message": "To authenticate with Gmail, please set up your Google Cloud credentials first.",
        "setup_instructions": "1. Go to Google Cloud Console\n2. Enable Gmail API\n3. Create OAuth 2.0 credentials\n4. Add credentials to .env file"
    }

@app.get("/auth/callback")
async def gmail_callback(code: str = None):
    """OAuth callback endpoint"""
    if code:
        return {"message": "Authentication successful! Gmail integration is now ready."}
    else:
        return {"message": "Authentication callback received. Please check your setup."}

@app.get("/auth/status")
async def auth_status():
    """Enhanced authentication status"""
    token_file = "tokens/default_token.json"
    has_token = os.path.exists(token_file)
    
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    credentials_configured = client_id and client_secret and client_id != "your_actual_client_id_here"
    
    if has_token:
        return {
            "authenticated": True,
            "message": "✅ Connected to real Gmail",
            "gmail_ready": True,
            "demo_mode": False
        }
    elif credentials_configured:
        return {
            "authenticated": False,
            "message": "🔗 Ready to connect your Gmail",
            "auth_url": "https://email-ethan-agent-production.up.railway.app/auth/gmail",  # Updated to production URL
            "gmail_configured": True,
            "demo_mode": True,
            "note": "Currently using demo data. Connect Gmail for real emails."
        }
    else:
        return {
            "authenticated": False,
            "message": "🎯 Using enhanced demo mode",
            "setup_required": False,
            "gmail_configured": False,
            "demo_mode": True,
            "note": "No Gmail setup needed for demo. Works out of the box!"
        }

@app.post("/a2a/agent")
async def a2a_endpoint(request: Request):
    """A2A endpoint with enhanced error handling and logging"""
    try:
        # Parse the request body
        body = await request.json()
        print(f"📨 Received A2A request: {body}")
        
        # Validate JSON-RPC 2.0 request
        if body.get("jsonrpc") != "2.0" or "id" not in body:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: jsonrpc must be '2.0' and id is required"
                    }
                }
            )
        
        # Create the request object
        rpc_request = JSONRPCRequest(**body)
        
        # Process with Email Ethan
        response = await email_ethan.handle_a2a_request(rpc_request)
        
        print(f"📤 Sending A2A response: {response}")
        return response.model_dump()
        
    except Exception as e:
        print(f"❌ A2A endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)}
                }
            }
        )

# Update discovery endpoint for Email Ethan
@app.get("/.well-known/agent.json")
async def agent_discovery():
    return {
        "name": "Email Ethan",
        "description": "AI-powered email management assistant that triages and summarizes your inbox",
        "url": "https://email-ethan-agent-production.up.railway.app",  # Production URL
        "version": "1.0.0",
        "provider": {
            "organization": "Holladworld",
            "url": "https://github.com/Holladworld"
        },
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": True
        },
        "skills": [
            {
                "id": "check_emails",
                "name": "Check Unread Emails",
                "description": "Fetch and display unread emails with priority categorization"
            },
            {
                "id": "summarize_emails", 
                "name": "Summarize Emails",
                "description": "Provide concise summaries of email content"
            },
            {
                "id": "categorize_emails",
                "name": "Categorize Emails", 
                "description": "Organize emails by priority and type"
            }
        ]
    }

# Keep existing health endpoints
@app.get("/")
async def root():
    return {
        "message": "Email Ethan API is running!", 
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "a2a_agent": "/a2a/agent", 
            "agent_discovery": "/.well-known/agent.json",
            "auth_status": "/auth/status"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "agent": "email-ethan",
        "timestamp": "2024-01-15T10:00:00Z",  # You can make this dynamic later
        "version": "1.0.0"
    }

# Add a simple test endpoint
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the API is working"""
    return {
        "message": "Email Ethan API is working!",
        "status": "success",
        "test_commands": [
            "Check my emails",
            "Summarize my inbox", 
            "What can you do?",
            "Categorize my emails"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=PORT, 
        reload=True,
        access_log=True  # Enable access logs for debugging
    )