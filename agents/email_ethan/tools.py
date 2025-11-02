import httpx
import base64
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re

class EmailTools:
    def __init__(self):
        # In a real implementation, you'd add Gmail API credentials here
        self.mock_emails = self._create_mock_emails()
    
    def _create_mock_emails(self) -> List[Dict[str, Any]]:
        """Create realistic mock emails for testing"""
        return [
            {
                "id": "1",
                "from": "accounting@company.com",
                "subject": "URGENT: Invoice #1234 Overdue",
                "snippet": "Your invoice payment is 30 days overdue. Please process immediately.",
                "body": "Dear Customer, Your invoice #1234 for $1,500 is 30 days overdue...",
                "date": "2024-01-15T09:00:00Z",
                "read": False
            },
            {
                "id": "2", 
                "from": "manager@company.com",
                "subject": "Meeting Reschedule Request",
                "snippet": "Can we move our 2pm meeting to 3pm? Let me know if that works.",
                "body": "Hi team, Due to a conflict, I need to reschedule our 2pm meeting...",
                "date": "2024-01-15T08:30:00Z",
                "read": False
            },
            {
                "id": "3",
                "from": "newsletter@technews.com", 
                "subject": "Weekly Tech Digest - AI Trends 2024",
                "snippet": "This week: New AI breakthroughs, developer tools, and industry insights",
                "body": "Welcome to your weekly tech digest! Here are the top stories...",
                "date": "2024-01-15T07:00:00Z",
                "read": False
            }
        ]
    
    async def fetch_emails(self, max_results: int = 10, unread_only: bool = True) -> List[Dict[str, Any]]:
        """Fetch emails (mock implementation - replace with real Gmail API)"""
        emails = self.mock_emails[:max_results]
        
        if unread_only:
            emails = [email for email in emails if not email["read"]]
        
        return emails
    
    def categorize_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize email by priority and type"""
        subject = email_data['subject'].lower()
        body = email_data['body'].lower()
        
        # Priority detection
        urgent_keywords = ['urgent', 'asap', 'emergency', 'important', 'deadline', 'overdue']
        newsletter_keywords = ['newsletter', 'digest', 'update', 'weekly', 'monthly']
        spam_keywords = ['unsubscribe', 'promotion', 'offer', 'discount', 'buy now']
        
        # Determine category
        if any(keyword in subject for keyword in urgent_keywords):
            category = 'urgent'
            priority = 5
        elif any(keyword in subject for keyword in newsletter_keywords):
            category = 'newsletter' 
            priority = 1
        elif any(keyword in body for keyword in spam_keywords):
            category = 'spam'
            priority = 1
        else:
            category = 'important'
            priority = 3
        
        return {
            'category': category,
            'priority': priority,
            'action_required': category in ['urgent', 'important'],
            'estimated_read_time': 2 if category == 'urgent' else 1
        }
    
    def summarize_email(self, email_content: str, max_points: int = 3) -> Dict[str, Any]:
        """Simple email summarization"""
        # Split into sentences and take key ones
        sentences = [s.strip() for s in email_content.split('.') if s.strip()]
        
        # Simple heuristic: take first, middle, and last sentences
        if len(sentences) <= max_points:
            key_points = sentences
        else:
            key_points = [
                sentences[0],  # First sentence (often the main point)
                sentences[len(sentences)//2],  # Middle sentence
                sentences[-1]  # Last sentence (often conclusion/call to action)
            ]
        
        return {
            'summary': f"Key points from email: {len(key_points)} main items",
            'key_points': key_points[:max_points],
            'sentiment': 'neutral'  # Could enhance with sentiment analysis later
        }
    
    def draft_quick_reply(self, original_email: Dict[str, Any], tone: str = 'professional') -> str:
        """Draft a quick reply based on email content"""
        category = self.categorize_email(original_email)['category']
        
        if category == 'urgent':
            return "Thank you for bringing this to my attention. I'm looking into it now and will get back to you shortly."
        elif 'meeting' in original_email['subject'].lower():
            return "I've received your meeting request. Let me check my calendar and confirm the timing."
        else:
            return "Thank you for your email. I'll review this and respond accordingly."