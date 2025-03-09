import os
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

class ZoomClient:
    """Client for interacting with the Zoom API to retrieve meeting transcripts"""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, account_id: Optional[str] = None):
        self.client_id = client_id or os.getenv("ZOOM_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("ZOOM_CLIENT_SECRET")
        self.account_id = account_id or os.getenv("ZOOM_ACCOUNT_ID")
        self.base_url = "https://api.zoom.us/v2"
        self.token = None
        self.token_expiry = None
        
        if not all([self.client_id, self.client_secret, self.account_id]):
            logger.warning("Zoom API credentials not fully configured")
    
    async def _get_access_token(self) -> str:
        """Get an access token from the Zoom API"""
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
            
        try:
            url = "https://zoom.us/oauth/token"
            auth = HTTPBasicAuth(self.client_id, self.client_secret)
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {"grant_type": "account_credentials", "account_id": self.account_id}
            
            response = requests.post(url, auth=auth, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"] - 300)  # Buffer of 5 minutes
            
            return self.token
        except Exception as e:
            logger.error(f"Error getting Zoom access token: {str(e)}")
            raise
    
    async def get_meetings(self, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Get meetings within a date range"""
        try:
            token = await self._get_access_token()
            
            url = f"{self.base_url}/users/me/meetings"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "type": "scheduled",
                "page_size": limit
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json().get("meetings", [])
        except Exception as e:
            logger.error(f"Error getting Zoom meetings: {str(e)}")
            return []
    
    async def get_meeting_transcript(self, meeting_id: str) -> Dict[str, Any]:
        """Get transcript for a specific meeting"""
        try:
            token = await self._get_access_token()
            
            # First, get the cloud recording info
            url = f"{self.base_url}/meetings/{meeting_id}/recordings"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            recording_data = response.json()
            
            # Look for transcript files
            transcript_files = []
            for recording_file in recording_data.get("recording_files", []):
                if recording_file.get("file_type") == "TRANSCRIPT":
                    transcript_files.append(recording_file)
            
            if not transcript_files:
                logger.warning(f"No transcript found for meeting {meeting_id}")
                return {"meeting_id": meeting_id, "transcript": "No transcript available"}
            
            # Get the actual transcript content
            # In a real implementation, we would download and parse the VTT file
            # For this example, we'll return mock transcript data
            return {
                "meeting_id": meeting_id,
                "topic": recording_data.get("topic", "Unknown Meeting"),
                "start_time": recording_data.get("start_time"),
                "duration": recording_data.get("duration"),
                "transcript": "This is a placeholder for the actual meeting transcript content."
            }
            
        except Exception as e:
            logger.error(f"Error getting Zoom meeting transcript: {str(e)}")
            return {"meeting_id": meeting_id, "transcript": f"Error retrieving transcript: {str(e)}"}
    
    async def get_recent_meeting_transcripts(self, days_back: int = 7, limit: int = 5) -> List[Dict[str, Any]]:
        """Get transcripts from recent meetings"""
        from_date = datetime.now() - timedelta(days=days_back)
        meetings = await self.get_meetings(from_date=from_date, limit=limit)
        
        transcripts = []
        for meeting in meetings[:limit]:
            meeting_id = meeting.get("id")
            if meeting_id:
                transcript = await self.get_meeting_transcript(meeting_id)
                transcripts.append(transcript)
        
        return transcripts 