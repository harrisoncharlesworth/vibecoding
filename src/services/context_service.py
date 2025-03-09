import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from src.integrations.zoom_client import ZoomClient
from src.integrations.gmail_client import GmailClient
from src.integrations.notion_client import NotionClient
from src.integrations.salesforce_client import SalesforceClient
from src.models.schemas import (
    ContextItem, EmailContext, MeetingContext, DocumentContext, 
    OpportunityContext, AccountContext, ContactContext,
    ContextRequest, ContextResponse
)

logger = logging.getLogger(__name__)

class ContextService:
    """Service for gathering context from integrated data sources"""
    
    def __init__(self):
        self.zoom_client = ZoomClient()
        self.gmail_client = GmailClient()
        self.notion_client = NotionClient()
        self.salesforce_client = SalesforceClient()
        
    async def get_context(self, request: ContextRequest) -> ContextResponse:
        """Get context from all sources based on the request"""
        context_items = []
        
        # Process sources to include (use all if not specified)
        sources = request.sources or ["zoom", "gmail", "notion", "salesforce"]
        
        # Process time range
        days_back = 7  # default
        if request.time_range:
            if "days_back" in request.time_range:
                days_back = int(request.time_range["days_back"])
        
        # Process entity focus
        entity_focus = None
        if request.entity_focus:
            entity_focus = request.entity_focus
        
        # Get context from Zoom if requested
        if "zoom" in sources:
            zoom_items = await self._get_zoom_context(request.query, days_back, request.limit)
            context_items.extend(zoom_items)
            
        # Get context from Gmail if requested
        if "gmail" in sources:
            gmail_items = await self._get_gmail_context(request.query, days_back, request.limit)
            context_items.extend(gmail_items)
            
        # Get context from Notion if requested
        if "notion" in sources:
            notion_items = await self._get_notion_context(request.query, request.limit)
            context_items.extend(notion_items)
            
        # Get context from Salesforce if requested
        if "salesforce" in sources:
            salesforce_items = await self._get_salesforce_context(request.query, entity_focus, days_back, request.limit)
            context_items.extend(salesforce_items)
        
        # Sort by timestamp (most recent first)
        context_items.sort(key=lambda x: x.timestamp if x.timestamp else datetime.min, reverse=True)
        
        # Apply limit if specified
        if request.limit and len(context_items) > request.limit:
            context_items = context_items[:request.limit]
        
        return ContextResponse(
            source="vibecoding-mcp",
            context_items=context_items,
            query=request.query,
            timestamp=datetime.now()
        )
    
    async def _get_zoom_context(self, query: Optional[str], days_back: int, limit: Optional[int]) -> List[ContextItem]:
        """Get context from Zoom meetings"""
        try:
            transcripts = await self.zoom_client.get_recent_meeting_transcripts(days_back=days_back, limit=limit or 5)
            
            # Convert to context items
            context_items = []
            for transcript in transcripts:
                # If there's a query, do a basic check if it's mentioned in the transcript
                if query and query.lower() not in transcript.get("transcript", "").lower():
                    continue
                    
                meeting_context = MeetingContext(
                    content=transcript.get("transcript", ""),
                    title=transcript.get("topic", "Unknown Meeting"),
                    participants=["Unknown"],  # In a real implementation, you'd extract participants
                    date=datetime.fromisoformat(transcript.get("start_time").replace("Z", "+00:00")) if transcript.get("start_time") else datetime.now(),
                    duration=transcript.get("duration", 0),
                    meeting_id=transcript.get("meeting_id", ""),
                    metadata={
                        "source": "zoom",
                        "date": transcript.get("start_time"),
                    }
                )
                context_items.append(meeting_context)
                
            return context_items
            
        except Exception as e:
            logger.error(f"Error getting context from Zoom: {str(e)}")
            return []
    
    async def _get_gmail_context(self, query: Optional[str], days_back: int, limit: Optional[int]) -> List[ContextItem]:
        """Get context from Gmail emails"""
        try:
            if query:
                emails = await self.gmail_client.search_emails(search_term=query, limit=limit or 10)
            else:
                emails = await self.gmail_client.get_recent_emails(days_back=days_back, limit=limit or 10)
            
            # Convert to context items
            context_items = []
            for email in emails:
                try:
                    # Parse date string into datetime (handling various formats)
                    date_str = email.get("date", "")
                    try:
                        date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    except ValueError:
                        # Fallback to now if we can't parse the date
                        date = datetime.now()
                    
                    email_context = EmailContext(
                        content=email.get("body", email.get("snippet", "")),
                        subject=email.get("subject", ""),
                        sender=email.get("from", ""),
                        recipients=[email.get("to", "")],  # In a real implementation, you'd parse this properly
                        date=date,
                        thread_id=email.get("thread_id", ""),
                        metadata={
                            "source": "gmail",
                            "id": email.get("id", ""),
                        }
                    )
                    context_items.append(email_context)
                except Exception as e:
                    logger.error(f"Error processing email: {str(e)}")
                    continue
                
            return context_items
            
        except Exception as e:
            logger.error(f"Error getting context from Gmail: {str(e)}")
            return []
    
    async def _get_notion_context(self, query: Optional[str], limit: Optional[int]) -> List[ContextItem]:
        """Get context from Notion documents"""
        try:
            # Search for pages, or just get recent pages from database
            if query:
                pages = await self.notion_client.search_pages(query=query, limit=limit or 10)
            else:
                pages = await self.notion_client.get_database_pages(limit=limit or 10)
            
            # Get content for each page
            context_items = []
            for page in pages:
                try:
                    page_id = page.get("id")
                    if not page_id:
                        continue
                        
                    # Get full page content
                    page_with_content = await self.notion_client.get_page_content(page_id)
                    
                    # Extract text content
                    content_blocks = page_with_content.get("content", [])
                    content_text = "\n".join([block.get("text", "") for block in content_blocks])
                    
                    # Parse last_edited_time
                    last_edited_str = page.get("last_edited_time", "")
                    try:
                        last_edited = datetime.fromisoformat(last_edited_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        last_edited = datetime.now()
                    
                    document_context = DocumentContext(
                        content=content_text,
                        title=page.get("title", "Untitled"),
                        authors=["Unknown"],  # In a real implementation, you'd get the actual authors
                        last_edited=last_edited,
                        page_id=page_id,
                        metadata={
                            "source": "notion",
                            "url": page.get("url", ""),
                            "created_time": page.get("created_time", ""),
                        }
                    )
                    context_items.append(document_context)
                except Exception as e:
                    logger.error(f"Error processing Notion page: {str(e)}")
                    continue
                
            return context_items
            
        except Exception as e:
            logger.error(f"Error getting context from Notion: {str(e)}")
            return []
    
    async def _get_salesforce_context(self, query: Optional[str], entity_focus: Optional[Dict[str, Any]], 
                                     days_back: int, limit: Optional[int]) -> List[ContextItem]:
        """Get context from Salesforce CRM"""
        try:
            context_items = []
            
            # Get focused entity if specified
            if entity_focus and "account_id" in entity_focus:
                # Get specific account
                account_id = entity_focus["account_id"]
                accounts = await self.salesforce_client.get_accounts(limit=1)
                
                # Get contacts for this account
                contacts = await self.salesforce_client.get_contacts(account_id=account_id, limit=limit or 5)
                
                # Add account context
                for account in accounts:
                    account_context = AccountContext(
                        content=account.get("Description", "No description available"),
                        name=account.get("Name", "Unknown Account"),
                        industry=account.get("Industry"),
                        website=account.get("Website"),
                        account_id=account.get("Id"),
                        metadata={
                            "source": "salesforce",
                            "type": account.get("Type"),
                            "phone": account.get("Phone"),
                            "last_modified": account.get("LastModifiedDate")
                        }
                    )
                    context_items.append(account_context)
                
                # Add contact contexts
                for contact in contacts:
                    contact_context = ContactContext(
                        content=f"Contact: {contact.get('FirstName', '')} {contact.get('LastName', '')}, {contact.get('Title', 'No title')}, {contact.get('Email', 'No email')}",
                        name=f"{contact.get('FirstName', '')} {contact.get('LastName', '')}",
                        email=contact.get("Email"),
                        phone=contact.get("Phone"),
                        title=contact.get("Title"),
                        account_name=contact.get("Account", {}).get("Name") if contact.get("Account") else None,
                        contact_id=contact.get("Id"),
                        metadata={
                            "source": "salesforce",
                            "department": contact.get("Department"),
                            "account_id": contact.get("AccountId"),
                            "last_modified": contact.get("LastModifiedDate")
                        }
                    )
                    context_items.append(contact_context)
            
            # Otherwise, get opportunities (possibly filtered by query)
            else:
                opportunities = await self.salesforce_client.get_opportunities(days_back=days_back, limit=limit or 5)
                
                # Add opportunity contexts
                for opp in opportunities:
                    # If query exists, check if it's mentioned in the opportunity name
                    if query and query.lower() not in opp.get("Name", "").lower():
                        continue
                        
                    # Parse dates
                    close_date = None
                    if opp.get("CloseDate"):
                        try:
                            close_date = datetime.strptime(opp.get("CloseDate"), "%Y-%m-%d")
                        except ValueError:
                            pass
                    
                    opportunity_context = OpportunityContext(
                        content=f"Opportunity: {opp.get('Name')}, Stage: {opp.get('StageName')}, Amount: {opp.get('Amount')}",
                        name=opp.get("Name", "Unknown Opportunity"),
                        stage=opp.get("StageName", "Unknown Stage"),
                        amount=float(opp.get("Amount")) if opp.get("Amount") else None,
                        close_date=close_date,
                        account_name=opp.get("Account", {}).get("Name") if opp.get("Account") else "Unknown Account",
                        owner_name=opp.get("Owner", {}).get("Name") if opp.get("Owner") else "Unknown Owner",
                        opportunity_id=opp.get("Id"),
                        metadata={
                            "source": "salesforce",
                            "account_id": opp.get("AccountId"),
                            "owner_id": opp.get("OwnerId"),
                            "last_modified": opp.get("LastModifiedDate")
                        }
                    )
                    context_items.append(opportunity_context)
            
            return context_items
        
        except Exception as e:
            logger.error(f"Error getting context from Salesforce: {str(e)}")
            return [] 