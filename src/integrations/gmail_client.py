import os
import logging
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

class GmailClient:
    """Client for interacting with the Gmail API to retrieve email context"""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, refresh_token: Optional[str] = None):
        self.client_id = client_id or os.getenv("GMAIL_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GMAIL_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("GMAIL_REFRESH_TOKEN")
        self.credentials = None
        self.service = None
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.warning("Gmail API credentials not fully configured")
    
    async def _get_service(self):
        """Get authenticated Gmail API service"""
        if self.service:
            return self.service
            
        try:
            creds = Credentials.from_authorized_user_info(
                {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                },
                scopes=["https://www.googleapis.com/auth/gmail.readonly"]
            )
            
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                
            self.credentials = creds
            self.service = build("gmail", "v1", credentials=creds)
            return self.service
            
        except Exception as e:
            logger.error(f"Error authenticating with Gmail API: {str(e)}")
            raise
    
    async def get_emails(self, query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
        """Get emails matching the given query"""
        try:
            service = await self._get_service()
            
            # List messages matching the query
            results = service.users().messages().list(
                userId="me", 
                q=query, 
                maxResults=max_results
            ).execute()
            
            messages = results.get("messages", [])
            
            # Get full details for each message
            emails = []
            for message in messages:
                msg = service.users().messages().get(
                    userId="me", 
                    id=message["id"],
                    format="full"
                ).execute()
                
                # Process headers to get metadata
                headers = msg["payload"]["headers"]
                
                # Helper function to get header value
                def get_header(name):
                    return next((h["value"] for h in headers if h["name"].lower() == name.lower()), None)
                
                # Get email body (simplified - just getting text parts in this example)
                body = ""
                if "parts" in msg["payload"]:
                    for part in msg["payload"]["parts"]:
                        if part["mimeType"] == "text/plain" and "data" in part["body"]:
                            body_data = part["body"]["data"]
                            body += base64.urlsafe_b64decode(body_data).decode("utf-8")
                elif "body" in msg["payload"] and "data" in msg["payload"]["body"]:
                    body_data = msg["payload"]["body"]["data"]
                    body = base64.urlsafe_b64decode(body_data).decode("utf-8")
                
                email_data = {
                    "id": msg["id"],
                    "thread_id": msg["threadId"],
                    "subject": get_header("Subject") or "(No Subject)",
                    "from": get_header("From") or "Unknown",
                    "to": get_header("To") or "Unknown",
                    "date": get_header("Date") or "Unknown",
                    "body": body,
                    "snippet": msg.get("snippet", "")
                }
                
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error getting emails from Gmail: {str(e)}")
            return []
    
    async def get_recent_emails(self, days_back: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emails from the past X days"""
        from_date = datetime.now() - timedelta(days=days_back)
        date_str = from_date.strftime("%Y/%m/%d")
        query = f"after:{date_str}"
        
        return await self.get_emails(query=query, max_results=limit)
    
    async def search_emails(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search emails with a specific term"""
        query = f"{search_term}"
        return await self.get_emails(query=query, max_results=limit) 