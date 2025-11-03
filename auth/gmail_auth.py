import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from fastapi import HTTPException

class GmailAuthenticator:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.client_config = {
            "web": {
                "client_id": os.getenv("GMAIL_CLIENT_ID", ""),
                "client_secret": os.getenv("GMAIL_CLIENT_SECRET", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
    def get_authorization_url(self):
        """Generate OAuth authorization URL"""
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES
            )
            
            flow.redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/auth/callback")
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return authorization_url
            
        except Exception as e:
            return None
    
    async def exchange_code_for_token(self, code: str):
        """Exchange authorization code for tokens"""
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES
            )
            
            flow.redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/auth/callback")
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Save credentials
            self._save_credentials(credentials)
            return credentials
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")
    
    def _save_credentials(self, credentials):
        """Save credentials to file"""
        tokens_dir = "tokens"
        os.makedirs(tokens_dir, exist_ok=True)
        
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        with open(f'{tokens_dir}/default_token.json', 'w') as token_file:
            token_file.write(json.dumps(creds_data))

# Create global authenticator instance
gmail_auth = GmailAuthenticator()