from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime  # ADD THIS IMPORT

from core.a2a_base import BaseA2AAgent
from models.a2a import TaskResult, TaskStatus, A2AMessage, MessagePart, Artifact
from .tools import EmailTools

class EmailEthanAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__("Email Ethan")
        self.tools = EmailTools()
        self.email_sessions = {}  # Track email conversations
    
    async def process_message(self, user_text: str, messages: list, context_id: Optional[str], task_id: Optional[str]) -> TaskResult:
        """Process email-related requests with better error handling"""
        try:
            context_id = context_id or str(uuid4())
            task_id = task_id or str(uuid4())

            print(f"🔍 DEBUG: Received message: '{user_text}'")
            
            # Enhanced command detection
            user_text_lower = user_text.lower().strip()
            
            # Determine what the user wants
            if any(cmd in user_text_lower for cmd in ['email', 'inbox', 'unread', 'message', 'read my', 'check my']):
                if any(cmd in user_text_lower for cmd in ['check', 'show', 'get', 'what', 'read my']):
                    result = await self._handle_check_emails(user_text)
                elif any(cmd in user_text_lower for cmd in ['summar', 'brief', 'overview']):
                    result = await self._handle_summarize_emails(user_text)
                elif any(cmd in user_text_lower for cmd in ['categor', 'priorit', 'organiz']):
                    result = await self._handle_categorize_emails(user_text)
                else:
                    result = await self._handle_check_emails(user_text)  # Default to check
            else:
                result = await self._handle_general_inquiry(user_text)
            
            # Build A2A response - ENSURING PROPER STRUCTURE
            response_message = A2AMessage(
                kind="message",
                role="agent",
                parts=[MessagePart(kind="text", text=result["response"])],
                messageId=str(uuid4()),
                taskId=task_id
            )
            
            # Build artifacts
            artifacts = []
            if "email_data" in result:
                artifacts.append(Artifact(
                    artifactId=str(uuid4()),
                    name="emailAnalysis",
                    parts=[MessagePart(kind="data", data={"emails": result["email_data"]})]
                ))
            
            # Build history
            history = []
            if messages:
                history.extend(messages)
            history.append(response_message)
            
            return TaskResult(
                id=task_id,
                contextId=context_id,
                status=TaskStatus(
                    state="completed",
                    timestamp=datetime.utcnow().isoformat() + "Z",  # Ensure proper timestamp
                    message=response_message
                ),
                artifacts=artifacts,
                history=history,
                kind="task"
            )
            
        except Exception as e:
            print(f"❌ ERROR in process_message: {str(e)}")
            # Return proper error response
            error_message = A2AMessage(
                kind="message",
                role="agent", 
                parts=[MessagePart(kind="text", text="Sorry, I encountered an error processing your request. Please try again.")],
                messageId=str(uuid4()),
                taskId=task_id or str(uuid4())
            )
            
            return TaskResult(
                id=task_id or str(uuid4()),
                contextId=context_id or str(uuid4()),
                status=TaskStatus(
                    state="failed",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    message=error_message
                ),
                artifacts=[],
                history=[],
                kind="task"
            )
    
    async def _handle_check_emails(self, user_text: str) -> Dict[str, Any]:
        """Handle email checking request"""
        # Extract number from user text if provided
        max_emails = 5
        if 'last' in user_text:
            try:
                max_emails = int([s for s in user_text.split() if s.isdigit()][0])
            except:
                pass
        
        emails = await self.tools.fetch_emails(max_results=max_emails, unread_only=True)
        
        # Check if using real Gmail or mock data
        using_real_gmail = any('@gmail.com' in email.get('from', '') for email in emails)
        
        # Categorize each email
        categorized_emails = []
        for email in emails:
            category_info = self.tools.categorize_email(email)
            categorized_emails.append({**email, **category_info})
        
        # Count by category
        urgent_count = len([e for e in categorized_emails if e['category'] == 'urgent'])
        important_count = len([e for e in categorized_emails if e['category'] == 'important'])
        
        # Build response
        if not categorized_emails:
            response_text = "🎉 Your inbox is clean! No unread emails."
        else:
            response_text = f"📧 Found {len(categorized_emails)} emails"
            if using_real_gmail:
                response_text += " (from your Gmail) 📱\n"
            else:
                response_text += " (demo data) 🎯\n"
                
            response_text += f"• {urgent_count} urgent • {important_count} important\n\n"
            
            # Show top emails
            for email in categorized_emails[:3]:
                icon = "🚨" if email['category'] == 'urgent' else "📌"
                response_text += f"{icon} {email['subject']}\n"
        
        # Add authentication hint if using mock data
        if not using_real_gmail:
            response_text += "\n💡 To connect your real Gmail: Visit /auth/gmail"
        
        return {
            "response": response_text,
            "email_data": categorized_emails,
            "categorized_emails": categorized_emails,
            "using_real_gmail": using_real_gmail
        }
    
    async def _handle_summarize_emails(self, user_text: str) -> Dict[str, Any]:
        """Handle email summarization request"""
        emails = await self.tools.fetch_emails(max_results=3, unread_only=True)
        
        if not emails:
            return {
                "response": "No emails to summarize. Your inbox is empty!",
                "email_data": []
            }
        
        summaries = []
        for email in emails:
            summary = self.tools.summarize_email(email['body'])
            summaries.append({
                'subject': email['subject'],
                'from': email['from'],
                'summary': summary['summary'],
                'key_points': summary['key_points']
            })
        
        response_text = f"📋 Summary of your {len(summaries)} most recent emails:\n\n"
        for i, summary in enumerate(summaries, 1):
            response_text += f"{i}. **{summary['subject']}** (from {summary['from']})\n"
            response_text += f"   {summary['summary']}\n"
            if summary['key_points']:
                response_text += f"   Key points: {'; '.join(summary['key_points'][:2])}\n"
            response_text += "\n"
        
        return {
            "response": response_text,
            "email_data": summaries
        }
    
    async def _handle_categorize_emails(self, user_text: str) -> Dict[str, Any]:
        """Handle email categorization request"""
        emails = await self.tools.fetch_emails(max_results=10, unread_only=True)
        
        categorized = []
        for email in emails:
            category_info = self.tools.categorize_email(email)
            categorized.append({
                'subject': email['subject'],
                'from': email['from'],
                'category': category_info['category'],
                'priority': category_info['priority'],
                'action_required': category_info['action_required']
            })
        
        # Group by category
        by_category = {}
        for email in categorized:
            cat = email['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(email)
        
        response_text = "🏷️ Email Categories:\n"
        for category, emails_in_category in by_category.items():
            response_text += f"\n{category.upper()} ({len(emails_in_category)}):\n"
            for email in emails_in_category[:2]:  # Show max 2 per category
                response_text += f"• {email['subject']}\n"
        
        return {
            "response": response_text,
            "categorized_emails": categorized
        }
    
    async def _handle_general_inquiry(self, user_text: str) -> Dict[str, Any]:
        """Handle general questions with better email detection"""
        user_text_lower = user_text.lower()
        
        # If they're asking about capabilities in different ways
        if any(phrase in user_text_lower for phrase in ['what can you do', 'help', 'capabilities', 'features']):
            return self._get_capabilities_response()
        
        # If they said "hello" or similar
        if any(greeting in user_text_lower for greeting in ['hello', 'hi', 'hey', 'greetings']):
            return {
                "response": "👋 Hey there! I'm Email Ethan, your email assistant!\n\nI can help you:\n• Check unread emails\n• Summarize your inbox\n• Categorize emails by priority\n\nTry asking: 'Check my emails' or 'What's in my inbox?'"
            }
        
        # Default helpful response
        return {
            "response": f"🤔 I'm not sure what you meant by '{user_text}'\n\nI'm Email Ethan - I specialize in email management! Here's what I can help with:\n\n📧 **Email Commands:**\n• 'Check my unread emails'\n• 'Summarize my inbox'  \n• 'Categorize my emails'\n• 'What's urgent in my inbox?'\n\n💡 **Just say 'emails' or 'inbox' and I'll jump right in!**"
        }
    
    def _get_capabilities_response(self):
        """Standard capabilities response"""
        return {
            "response": "🤖 **I'm Email Ethan - Your AI Email Assistant!**\n\nHere's what I can do:\n\n📋 **Email Management**\n• Check and count unread emails\n• Categorize by urgency (🚨 Urgent, 📌 Important, 📰 Newsletter)\n• Summarize long emails into key points\n• Identify action-required messages\n\n🔧 **How to use me:**\nJust ask naturally!\n• 'Check my emails'\n• 'What's in my inbox?'\n• 'Summarize my unread messages'\n• 'Show me urgent emails'\n\nI work with demo data by default, but can connect to your real Gmail if you want!"
        }