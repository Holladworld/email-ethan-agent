# core/a2a_base.py
from models.a2a import JSONRPCRequest, JSONRPCResponse, TaskResult, TaskStatus, A2AMessage, MessagePart
from uuid import uuid4
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseA2AAgent:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.sessions = {}  # In-memory session storage
    
    async def handle_a2a_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """REUSABLE: Handle any A2A request - same for all agents"""
        try:
            logger.info(f"Processing A2A request for agent: {self.agent_name}")
            
            # Extract the user message
            user_message = request.params.get("message", {})
            user_text = ""
            
            for part in user_message.get("parts", []):
                if part.get("kind") == "text":
                    user_text = part.get("text", "")
                    break
            
            # Process with the specific agent logic
            result = await self.process_message(
                user_text=user_text,
                messages=[user_message],
                context_id=request.params.get("contextId"),
                task_id=user_message.get("taskId")  # Fixed: get taskId from message
            )
            
            return JSONRPCResponse(
                id=request.id,
                result=result
            )
            
        except Exception as e:
            logger.error(f"Error processing A2A request: {e}")
            return JSONRPCResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)}
                }
            )
    
    async def process_message(self, user_text: str, messages: list, context_id: Optional[str], task_id: Optional[str]) -> TaskResult:
        """REUSABLE: Template method - child classes implement specific logic"""
        raise NotImplementedError("Child classes must implement process_message")