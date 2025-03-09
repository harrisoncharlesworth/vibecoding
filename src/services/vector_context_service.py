import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.services.context_service import ContextService
from src.services.vector_store import VectorStore
from src.models.schemas import ContextRequest, ContextResponse, ContextItem

logger = logging.getLogger(__name__)

class VectorContextService:
    """Advanced context service using vector embedding for semantic search"""
    
    def __init__(self):
        self.context_service = ContextService()
        self.vector_store = VectorStore()
        self.initialized = False
    
    async def initialize(self, days_back: int = 30) -> None:
        """Initialize the vector store with existing context data"""
        if self.initialized:
            return
            
        # Get context from all sources with a wide time range
        request = ContextRequest(
            time_range={"days_back": days_back},
            sources=["zoom", "gmail", "notion", "salesforce"],
            limit=100  # Get a substantial amount of initial data
        )
        
        response = await self.context_service.get_context(request)
        
        # Convert to dicts for vector store
        context_dicts = [item.dict() for item in response.context_items]
        
        # Add to vector store
        self.vector_store.add_items(context_dicts)
        
        self.initialized = True
        logger.info(f"Vector context service initialized with {len(context_dicts)} items")
    
    async def get_context(self, request: ContextRequest) -> ContextResponse:
        """Get context using vector search for better relevance"""
        # Initialize if needed
        if not self.initialized:
            await self.initialize()
        
        # If no query is provided, fall back to regular context service
        if not request.query:
            return await self.context_service.get_context(request)
        
        # Set up filter criteria based on request
        filter_criteria = {}
        if request.sources:
            filter_criteria["source"] = request.sources[0] if len(request.sources) == 1 else None
        
        # Perform vector search
        vector_results = self.vector_store.search(
            query=request.query,
            filter_criteria=filter_criteria,
            limit=request.limit or 10
        )
        
        if not vector_results:
            # If no vector results, fall back to regular context
            logger.info(f"No vector results for query '{request.query}', falling back to regular context service")
            return await self.context_service.get_context(request)
        
        # Convert results back to ContextItems
        context_items = []
        for result in vector_results:
            # Extract metadata
            metadata = result.get("metadata", {})
            item_type = metadata.get("type", "unknown")
            source = metadata.get("source", "unknown")
            
            # Create basic ContextItem with all mandatory fields
            # In a real implementation, you'd reconstruct the specific context type
            item = ContextItem(
                type=item_type,
                source=source,
                content=result.get("content", ""),
                metadata={
                    **metadata,
                    "vector_score": result.get("score", 0.0)
                }
            )
            context_items.append(item)
        
        # Also get fresh context from sources if requested
        if request.time_range and request.time_range.get("include_fresh", False):
            fresh_response = await self.context_service.get_context(request)
            
            # Add fresh results and deduplicate
            existing_ids = set(item.metadata.get("id", "") for item in context_items if item.metadata.get("id"))
            for item in fresh_response.context_items:
                item_id = ""
                if hasattr(item, "thread_id"):
                    item_id = item.thread_id
                elif hasattr(item, "meeting_id"):
                    item_id = item.meeting_id
                elif hasattr(item, "page_id"):
                    item_id = item.page_id
                
                if item_id and item_id not in existing_ids:
                    context_items.append(item)
                    existing_ids.add(item_id)
        
        # Create response
        return ContextResponse(
            source="vibecoding-mcp-vector",
            context_items=context_items,
            query=request.query,
            timestamp=datetime.now()
        )
    
    async def add_to_index(self, context_items: List[ContextItem]) -> None:
        """Add new context items to the vector index"""
        # Convert to dicts for vector store
        context_dicts = [item.dict() for item in context_items]
        
        # Add to vector store
        self.vector_store.add_items(context_dicts)
        logger.info(f"Added {len(context_dicts)} new items to vector index") 