from fastapi import FastAPI, Request  # <-- Add Request here
from fastapi.responses import JSONResponse
import uvicorn
from uuid import uuid4  # <-- Add this import too

from models.a2a import JSONRPCRequest
from core.a2a_base import BaseA2AAgent

# REUSABLE: This setup works for any agent
app = FastAPI(
    title="AI Agent API",
    description="Reusable A2A agent framework",
    version="1.0.0"
)

# We'll replace this with Email Ethan in Stage 3
class SimpleTestAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__("SimpleTestAgent")
    
    async def process_message(self, user_text: str, messages: list, context_id, task_id):
        from models.a2a import TaskResult, TaskStatus, A2AMessage, MessagePart, Artifact
        
        # Simple echo agent for testing
        response_message = A2AMessage(
            role="agent",
            parts=[MessagePart(kind="text", text=f"You said: {user_text}")],
            taskId=task_id
        )
        
        return TaskResult(
            id=task_id or str(uuid4()),
            contextId=context_id or str(uuid4()),
            status=TaskStatus(
                state="completed",
                message=response_message
            ),
            history=messages + [response_message]
        )

# Initialize our test agent with test id error handling
@app.post("/a2a/agent")
async def a2a_endpoint(request: Request):
    """REUSABLE: A2A endpoint that works for any agent"""
    try:
        body = await request.json()
        
        # Get request ID early for error handling
        request_id = body.get("id", "unknown")
        
        # Validate JSON-RPC 2.0 basics first
        if body.get("jsonrpc") != "2.0" or not request_id:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: jsonrpc must be '2.0' and id is required"
                    }
                }
            )
        
        # Now parse with Pydantic
        rpc_request = JSONRPCRequest(**body)
        
        response = await test_agent.handle_a2a_request(rpc_request)
        return response.model_dump()
        
    except Exception as e:
        # Extract request ID from body if available
        request_id = "unknown"
        try:
            if 'body' in locals():
                request_id = body.get("id", "unknown")
        except:
            pass
            
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)}
                }
            }
        )
    
    # OR This ORIGINAL SIMPLER VERSION:
    # This is without id for error handling improvements
    # try:
    
# test_agent = SimpleTestAgent()

# @app.post("/a2a/agent")
# async def a2a_endpoint(request: Request):
#     """REUSABLE: A2A endpoint that works for any agent"""
#     try:
#         body = await request.json()
#         rpc_request = JSONRPCRequest(**body)
        
#         response = await test_agent.handle_a2a_request(rpc_request)
#         return response.model_dump()
        
#     except Exception as e:
#         return JSONResponse(
#             status_code=500,
#             content={
#                 "jsonrpc": "2.0",
#                 "id": None,
#                 "error": {
#                     "code": -32603,
#                     "message": "Internal error",
#                     "data": {"details": str(e)}
#                 }
#             }
#         )

# Keep your existing endpoints (they're already reusable)
@app.get("/")
async def root():
    return {"message": "Reusable AI Agent API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "reusable-framework"}

@app.get("/.well-known/agent.json")
async def agent_discovery():
    return {
        "name": "Reusable Agent Framework",
        "description": "Base framework for building A2A agents",
        "url": "http://localhost:8000",
        "version": "1.0.0",
        "provider": {"organization": "Holladworld"}
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)