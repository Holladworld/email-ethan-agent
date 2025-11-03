from models.a2a import JSONRPCRequest, JSONRPCResponse, TaskResult, TaskStatus, A2AMessage, MessagePart
from uuid import uuid4
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseA2AAgent:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.sessions = {}
    
    async def handle_a2a_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle A2A requests - FIXED version"""
        try:
            logger.info(f"Processing A2A request: {request.id}")
            
            # FIX: Properly access the message from params
            user_message = None
            user_text = ""
            
            # Handle different param structures safely
            if hasattr(request.params, 'message'):
                user_message = request.params.message
            elif hasattr(request.params, 'messages') and request.params.messages:
                user_message = request.params.messages[-1]  # Take last message
            else:
                return JSONRPCResponse(
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid params: no message found",
                        "data": {"details": "Request must include a message"}
                    }
                )
            
            # Extract text from message parts
            if user_message and hasattr(user_message, 'parts'):
                for part in user_message.parts:
                    if hasattr(part, 'kind') and part.kind == "text" and hasattr(part, 'text'):
                        user_text = part.text or ""
                        break
            
            # Get context and task IDs safely
            context_id = None
            task_id = None
            
            if hasattr(request.params, 'contextId'):
                context_id = request.params.contextId
            if user_message and hasattr(user_message, 'taskId'):
                task_id = user_message.taskId
            
            # Process with specific agent logic
            result = await self.process_message(
                user_text=user_text,
                messages=[user_message] if user_message else [],
                context_id=context_id,
                task_id=task_id
            )
            
            return JSONRPCResponse(
                id=request.id,
                result=result
            )
            
        except Exception as e:
            logger.error(f"A2A handler error: {str(e)}")
            return JSONRPCResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)}
                }
            )
    
    async def process_message(self, user_text: str, messages: list, context_id: Optional[str], task_id: Optional[str]) -> TaskResult:
        """Template method - child classes implement specific logic"""
        raise NotImplementedError("Child classes must implement process_message")