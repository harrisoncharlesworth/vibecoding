import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from notion_client import Client as NotionSDKClient

logger = logging.getLogger(__name__)

class NotionClient:
    """Client for interacting with the Notion API to retrieve document context"""
    
    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.client = None
        
        if not all([self.api_key, self.database_id]):
            logger.warning("Notion API credentials not fully configured")
    
    async def _get_client(self):
        """Get authenticated Notion client"""
        if self.client:
            return self.client
            
        try:
            self.client = NotionSDKClient(auth=self.api_key)
            return self.client
        except Exception as e:
            logger.error(f"Error initializing Notion client: {str(e)}")
            raise
    
    async def get_database_pages(self, filter_params: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pages from a Notion database"""
        try:
            client = await self._get_client()
            
            # Query the database
            query_params = {
                "database_id": self.database_id,
                "page_size": limit
            }
            
            if filter_params:
                query_params["filter"] = filter_params
                
            response = client.databases.query(**query_params)
            
            # Process and return the results
            pages = []
            for result in response.get("results", []):
                page_id = result.get("id")
                
                # Extract properties (simplified - actual implementation would need to handle various property types)
                properties = result.get("properties", {})
                title = ""
                
                # Find the title property (usually called "Name" or "Title")
                for prop_name, prop_data in properties.items():
                    if prop_data.get("type") == "title":
                        title_items = prop_data.get("title", [])
                        title = "".join([item.get("plain_text", "") for item in title_items])
                        break
                
                created_time = result.get("created_time")
                last_edited_time = result.get("last_edited_time")
                
                page_data = {
                    "id": page_id,
                    "title": title,
                    "created_time": created_time,
                    "last_edited_time": last_edited_time,
                    "url": result.get("url")
                }
                
                pages.append(page_data)
            
            return pages
            
        except Exception as e:
            logger.error(f"Error getting pages from Notion database: {str(e)}")
            return []
    
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Get content from a specific Notion page"""
        try:
            client = await self._get_client()
            
            # Get the page
            page = client.pages.retrieve(page_id=page_id)
            
            # Get the page content blocks
            blocks = client.blocks.children.list(block_id=page_id).get("results", [])
            
            # Process block content (simplified)
            content = []
            for block in blocks:
                block_type = block.get("type")
                if not block_type:
                    continue
                    
                block_content = block.get(block_type, {})
                if "rich_text" in block_content:
                    text_items = block_content.get("rich_text", [])
                    text = "".join([item.get("plain_text", "") for item in text_items])
                    content.append({
                        "type": block_type,
                        "text": text
                    })
                elif block_type == "heading_1" or block_type == "heading_2" or block_type == "heading_3":
                    text_items = block_content.get("rich_text", [])
                    text = "".join([item.get("plain_text", "") for item in text_items])
                    content.append({
                        "type": block_type,
                        "text": text
                    })
            
            # Extract properties for metadata
            properties = page.get("properties", {})
            title = ""
            
            # Find the title property
            for prop_name, prop_data in properties.items():
                if prop_data.get("type") == "title":
                    title_items = prop_data.get("title", [])
                    title = "".join([item.get("plain_text", "") for item in title_items])
                    break
            
            return {
                "id": page_id,
                "title": title,
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "content": content,
                "url": page.get("url")
            }
            
        except Exception as e:
            logger.error(f"Error getting content from Notion page: {str(e)}")
            return {"id": page_id, "error": str(e)}
    
    async def search_pages(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for Notion pages matching a query"""
        try:
            client = await self._get_client()
            
            # Search Notion
            search_params = {
                "query": query,
                "page_size": limit,
                "filter": {
                    "property": "object",
                    "value": "page"
                }
            }
            
            response = client.search(**search_params)
            
            # Process and return the results (similar to get_database_pages)
            pages = []
            for result in response.get("results", []):
                page_id = result.get("id")
                
                # Extract properties
                properties = result.get("properties", {})
                title = ""
                
                # Find the title property
                for prop_name, prop_data in properties.items():
                    if prop_data.get("type") == "title":
                        title_items = prop_data.get("title", [])
                        title = "".join([item.get("plain_text", "") for item in title_items])
                        break
                
                created_time = result.get("created_time")
                last_edited_time = result.get("last_edited_time")
                
                page_data = {
                    "id": page_id,
                    "title": title,
                    "created_time": created_time,
                    "last_edited_time": last_edited_time,
                    "url": result.get("url")
                }
                
                pages.append(page_data)
            
            return pages
            
        except Exception as e:
            logger.error(f"Error searching Notion: {str(e)}")
            return [] 