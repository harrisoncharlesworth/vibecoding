from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ContextItem(BaseModel):
    """Base model for a context item from any source"""
    type: str = Field(..., description="Type of context item (email, meeting, document, etc.)")
    source: str = Field(..., description="Source of the context (gmail, zoom, notion, etc.)")
    content: str = Field(..., description="The actual content of the context item")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the context item")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="When this context was created/retrieved")

class EmailContext(ContextItem):
    """Model for email context from Gmail"""
    type: str = "email"
    source: str = "gmail"
    subject: str = Field(..., description="Email subject")
    sender: str = Field(..., description="Email sender")
    recipients: List[str] = Field(..., description="Email recipients")
    date: datetime = Field(..., description="Email date")
    thread_id: Optional[str] = Field(None, description="Email thread ID")

class MeetingContext(ContextItem):
    """Model for meeting context from Zoom"""
    type: str = "meeting"
    source: str = "zoom"
    title: str = Field(..., description="Meeting title")
    participants: List[str] = Field(..., description="Meeting participants")
    date: datetime = Field(..., description="Meeting date")
    duration: int = Field(..., description="Meeting duration in minutes")
    meeting_id: str = Field(..., description="Zoom meeting ID")

class DocumentContext(ContextItem):
    """Model for document context from Notion"""
    type: str = "document"
    source: str = "notion"
    title: str = Field(..., description="Document title")
    authors: List[str] = Field(..., description="Document authors")
    last_edited: datetime = Field(..., description="Last edit timestamp")
    page_id: str = Field(..., description="Notion page ID")

# New Salesforce context models
class OpportunityContext(ContextItem):
    """Model for opportunity context from Salesforce"""
    type: str = "opportunity"
    source: str = "salesforce"
    name: str = Field(..., description="Opportunity name")
    stage: str = Field(..., description="Opportunity stage")
    amount: Optional[float] = Field(None, description="Opportunity amount")
    close_date: Optional[datetime] = Field(None, description="Expected close date")
    account_name: str = Field(..., description="Account name")
    owner_name: str = Field(..., description="Opportunity owner")
    opportunity_id: str = Field(..., description="Salesforce opportunity ID")

class AccountContext(ContextItem):
    """Model for account context from Salesforce"""
    type: str = "account"
    source: str = "salesforce"
    name: str = Field(..., description="Account name")
    industry: Optional[str] = Field(None, description="Account industry")
    website: Optional[str] = Field(None, description="Account website")
    account_id: str = Field(..., description="Salesforce account ID")
    description: Optional[str] = Field(None, description="Account description")

class ContactContext(ContextItem):
    """Model for contact context from Salesforce"""
    type: str = "contact"
    source: str = "salesforce"
    name: str = Field(..., description="Contact name")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    title: Optional[str] = Field(None, description="Contact title")
    account_name: Optional[str] = Field(None, description="Account name")
    contact_id: str = Field(..., description="Salesforce contact ID")

class ContextRequest(BaseModel):
    """Model for incoming context requests"""
    query: Optional[str] = Field(None, description="Natural language query to filter context by")
    time_range: Optional[Dict[str, Any]] = Field(None, description="Time range to filter context by")
    sources: Optional[List[str]] = Field(None, description="Sources to include in context gathering")
    limit: Optional[int] = Field(10, description="Maximum number of context items to return")
    entity_focus: Optional[Dict[str, Any]] = Field(None, description="Specific entity to focus on (e.g., account_id)")
    
class ContextResponse(BaseModel):
    """Model for outgoing context responses"""
    source: str = Field("vibecoding-mcp", description="Source of this context response")
    context_items: List[ContextItem] = Field(..., description="List of context items")
    query: Optional[str] = Field(None, description="Original query if provided")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this response was generated") 