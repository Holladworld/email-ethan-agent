from typing import List, Optional, Dict, Any
from uuid import uuid4

from core.a2a_base import BaseA2AAgent
from models.a2a import TaskResult, TaskStatus, A2AMessage, MessagePart, Artifact
from .tools import EmailTools

class EmailEthanAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__("Email Ethan")
        self.tools = EmailTools()
        self.email_sessions = {}  # Track email conversations
    
    async def process_message(self, user_text: str, messages: list, context_id: Optional[str], task_id: Optional[str]) -> TaskResult:
        """Process email-related requests - Email Ethan's specific logic"""
        context_id = context_id or str(uuid4())
        task_id = task_id or str(uuid4())
        
        # Determine what the user wants
        user_text_lower = user_text.lower()
        
        if any(cmd in user_text_lower for cmd in ['unread', 'check email', 'new email', 'inbox']):
            result = await self._handle_check_emails(user_text)
        elif any(cmd in user_text_lower for cmd in ['summarize', 'summary']):
            result = await self._handle_summarize_emails(user_text)
        elif any(cmd in user_text_lower for cmd in ['categorize', 'priority']):
            result = await self._handle_categorize_emails(user_text)
        else:
            result = await self._handle_general_inquiry(user_text)
        
        # Build A2A response
        response_message = A2AMessage(
            role="agent",
            parts=[MessagePart(kind="text", text=result["response"])],
            taskId=task_id
        )
        
        
        # Build artifacts with email data - FIXED: Properly structure data
        artifacts = []
        if "email_data" in result:
            artifacts.append(Artifact(
                name="emailAnalysis",
                parts=[MessagePart(kind="data", data={"emails": result["email_data"]})]  # Wrap in dict
            ))

        if "categorized_emails" in result:
            artifacts.append(Artifact(
                name="categorizedEmails", 
                parts=[MessagePart(kind="data", data={"categorized": result["categorized_emails"]})]  # Wrap in dict
            ))

        
        return TaskResult(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(
                state="completed",
                message=response_message
            ),
            artifacts=artifacts,
            history=messages + [response_message]
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
            response_text = f"📧 You have {len(categorized_emails)} unread emails:\n"
            response_text += f"• {urgent_count} urgent\n"
            response_text += f"• {important_count} important\n"
            response_text += f"• {len(categorized_emails) - urgent_count - important_count} others\n\n"
            
            # Show urgent emails first
            urgent_emails = [e for e in categorized_emails if e['category'] == 'urgent']
            for email in urgent_emails[:2]:  # Show max 2 urgent emails
                response_text += f"🚨 {email['subject']} (from {email['from']})\n"
        
        return {
            "response": response_text,
            "email_data": categorized_emails,
            "categorized_emails": categorized_emails
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
        """Handle general email-related questions"""
        capabilities = [
            "Check unread emails",
            "Summarize email content", 
            "Categorize emails by priority",
            "Identify urgent messages",
            "Draft quick replies"
        ]
        
        response_text = f"🤖 I'm Email Ethan, your email assistant!\n\nI can help you with:\n"
        for capability in capabilities:
            response_text += f"• {capability}\n"
        
        response_text += f"\nYou asked: '{user_text}'\nTry: 'Check my unread emails' or 'Summarize my inbox'"
        
        return {"response": response_text}