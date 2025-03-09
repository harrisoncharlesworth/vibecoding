import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime

from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector database for semantic search over context items"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        self.vector_db = None
        self.documents = []
    
    def add_items(self, context_items: List[Dict[str, Any]]) -> None:
        """Add context items to the vector store"""
        documents = []
        
        for item in context_items:
            # Extract content and metadata
            content = item.get("content", "")
            if not content:
                continue
                
            # Create metadata dictionary
            metadata = {
                "source": item.get("source", "unknown"),
                "type": item.get("type", "unknown"),
                "id": item.get("id", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add specific fields based on type
            if item.get("type") == "email":
                metadata["subject"] = item.get("subject", "")
                metadata["sender"] = item.get("sender", "")
                metadata["date"] = item.get("date", "")
            elif item.get("type") == "meeting":
                metadata["title"] = item.get("title", "")
                metadata["date"] = item.get("date", "")
            elif item.get("type") == "document":
                metadata["title"] = item.get("title", "")
                metadata["last_edited"] = item.get("last_edited", "")
            elif item.get("type") in ["opportunity", "account", "contact"]:
                metadata["name"] = item.get("name", "")
            
            # Split content into chunks if it's long
            texts = self.text_splitter.split_text(content)
            
            # Create documents for each chunk
            for i, text in enumerate(texts):
                doc = Document(
                    page_content=text,
                    metadata={
                        **metadata,
                        "chunk": i,
                        "total_chunks": len(texts)
                    }
                )
                documents.append(doc)
        
        # Add to tracking list
        self.documents.extend(documents)
        
        # Create or update vector database
        if self.vector_db is None:
            self.vector_db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory="./data/chroma"
            )
        else:
            self.vector_db.add_documents(documents)
    
    def search(self, query: str, filter_criteria: Optional[Dict[str, Any]] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for context items semantically related to the query"""
        if self.vector_db is None or not self.documents:
            logger.warning("Vector database is empty, no results to return")
            return []
            
        # Process filter criteria if provided
        filter_dict = {}
        if filter_criteria:
            for key, value in filter_criteria.items():
                if key in ["source", "type"]:
                    filter_dict[key] = value
        
        # Perform the search
        try:
            results = self.vector_db.similarity_search(
                query=query,
                k=limit,
                filter=filter_dict if filter_dict else None
            )
            
            # Process results
            processed_results = []
            for doc in results:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": doc.metadata.get("score", 0.0) if hasattr(doc, "metadata") else 0.0
                }
                processed_results.append(result)
                
            return processed_results
        except Exception as e:
            logger.error(f"Error during vector search: {str(e)}")
            return [] 