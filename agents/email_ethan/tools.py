import httpx
import base64
import json
import os
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class EmailTools:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    async def fetch_emails(self, max_results: int = 10, unread_only: bool = True) -> List[Dict[str, Any]]:
        """Smart email fetcher - tries real Gmail, falls back to mock data"""
        try:
            # Try to get real Gmail data first
            real_emails = await self._fetch_real_gmail_emails(max_results, unread_only)
            if real_emails:
                print("✅ Using REAL Gmail data")
                return real_emails
        except Exception as e:
            print(f"⚠️ Gmail not available, using mock data: {e}")
        
        # Fallback to enhanced mock data
        print("📧 Using ENHANCED mock email data")
        return self._get_enhanced_mock_emails()[:max_results]
    
    async def _fetch_real_gmail_emails(self, max_results: int, unread_only: bool) -> Optional[List[Dict[str, Any]]]:
        """Try to fetch real Gmail emails"""
        try:
            token_file = 'tokens/default_token.json'
            if not os.path.exists(token_file):
                return None
            
            # Load credentials
            with open(token_file, 'r') as f:
                creds_data = json.load(f)
            
            credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data['refresh_token'],
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes']
            )
            
            # Refresh if needed
            if credentials.expired:
                credentials.refresh(Request())
            
            # Make API call
            query = "is:unread" if unread_only else ""
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults={max_results}&q={query}',
                    headers={'Authorization': f'Bearer {credentials.token}'}
                )
                
                if response.status_code == 200:
                    messages_data = response.json()
                    emails = []
                    
                    for msg in messages_data.get('messages', [])[:max_results]:
                        # Get full message
                        msg_response = await client.get(
                            f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg["id"]}',
                            headers={'Authorization': f'Bearer {credentials.token}'}
                        )
                        
                        if msg_response.status_code == 200:
                            email_info = await self._parse_gmail_message(msg_response.json())
                            emails.append(email_info)
                    
                    return emails
                
        except Exception as e:
            print(f"Gmail API error: {e}")
        
        return None
    
    def _get_enhanced_mock_emails(self) -> List[Dict[str, Any]]:
        """Return realistic mock emails that demonstrate all features"""
        return [
            {
                "id": "mock_1",
                "from": "ceo@company.com",
                "subject": "URGENT: Quarterly Strategy Meeting",
                "snippet": "We need to discuss Q4 goals and budget allocation. Please review the attached deck.",
                "body": "Hi team, Our quarterly strategy meeting is scheduled for Friday. I've attached the presentation deck with our Q4 goals, budget projections, and key initiatives. Please review and come prepared to discuss.",
                "date": "2024-01-15T10:00:00Z",
                "read": False
            },
            {
                "id": "mock_2",
                "from": "engineering@tech.com",
                "subject": "🚀 Project Phoenix: Deployment Successful",
                "snippet": "The new AI features are now live in production. Great work everyone!",
                "body": "Team, I'm thrilled to announce that Project Phoenix deployment was successful! All AI features are now live. Performance metrics look excellent. Special thanks to the backend team for the smooth rollout.",
                "date": "2024-01-15T09:30:00Z", 
                "read": False
            },
            {
                "id": "mock_3",
                "from": "hr@company.com",
                "subject": "Benefits Enrollment Reminder",
                "snippet": "Open enrollment ends Friday. Don't forget to select your healthcare plan.",
                "body": "This is a reminder that open enrollment for health benefits ends this Friday. Please log into the portal to review and select your plans for 2024.",
                "date": "2024-01-15T08:00:00Z",
                "read": True
            },
            {
                "id": "mock_4", 
                "from": "newsletter@aiweekly.com",
                "subject": "AI Weekly: Latest in Machine Learning",
                "snippet": "This week: New transformer architectures, ethical AI frameworks, and industry news",
                "body": "Welcome to AI Weekly! In this edition: 1) New transformer models breaking benchmarks 2) Ethical AI frameworks gaining traction 3) Industry partnerships and acquisitions",
                "date": "2024-01-15T07:00:00Z",
                "read": False
            },
            {
                "id": "mock_5",
                "from": "security@company.com", 
                "subject": "🔒 Security Alert: Password Reset Required",
                "snippet": "Action required: Reset your password due to recent security update",
                "body": "As part of our enhanced security measures, all employees must reset their passwords by EOD Friday. Please use the password reset portal.",
                "date": "2024-01-14T16:00:00Z",
                "read": False
            }
        ]
    
    # Keep your existing categorize_email and summarize_email methods
    def categorize_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize email by priority and type"""
        subject = email_data['subject'].lower()
        body = email_data['body'].lower()
        
        urgent_keywords = ['urgent', 'asap', 'emergency', 'alert', 'required', 'reset']
        newsletter_keywords = ['newsletter', 'weekly', 'digest', 'update']
        
        if any(keyword in subject for keyword in urgent_keywords):
            category = 'urgent'
            priority = 5
        elif any(keyword in subject for keyword in newsletter_keywords):
            category = 'newsletter'
            priority = 1
        elif 'project' in subject or 'deployment' in subject:
            category = 'important' 
            priority = 4
        else:
            category = 'important'
            priority = 3
        
        return {
            'category': category,
            'priority': priority,
            'action_required': category in ['urgent', 'important'],
            'estimated_read_time': max(1, len(body) // 500)
        }
    
    def summarize_email(self, email_content: str, max_points: int = 3) -> Dict[str, Any]:
        """Enhanced summarization"""
        sentences = [s.strip() for s in email_content.split('.') if s.strip() and len(s) > 10]
        
        if len(sentences) <= max_points:
            key_points = sentences
        else:
            key_points = [sentences[0], sentences[len(sentences)//2], sentences[-1]]
        
        return {
            'summary': f"Key insights from email ({len(key_points)} main points)",
            'key_points': key_points[:max_points],
            'sentiment': 'neutral'
        }
    
    async def _parse_gmail_message(self, message_data: Dict) -> Dict[str, Any]:
        """Parse real Gmail message"""
        headers = {}
        for header in message_data.get('payload', {}).get('headers', []):
            headers[header['name'].lower()] = header['value']
        
        body = message_data.get('snippet', '')
        
        return {
            'id': message_data['id'],
            'from': headers.get('from', ''),
            'subject': headers.get('subject', ''),
            'date': headers.get('date', ''),
            'snippet': message_data.get('snippet', ''),
            'body': body,
            'read': 'UNREAD' not in message_data.get('labelIds', [])
        }