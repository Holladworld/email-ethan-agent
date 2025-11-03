from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
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

# Simple authentication endpoints (we'll enhance these later)
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
            "auth_url": "http://localhost:8000/auth/gmail", 
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
    """A2A endpoint now powered by Email Ethan"""
    try:
        body = await request.json()
        rpc_request = JSONRPCRequest(**body)
        
        response = await email_ethan.handle_a2a_request(rpc_request)
        return response.model_dump()
        
    except Exception as e:
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
        "url": "http://localhost:8000",  # Using localhost for now
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
    return {"message": "Email Ethan API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "email-ethan"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)