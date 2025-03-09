import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv

from src.services.context_service import ContextService
from src.services.vector_context_service import VectorContextService
from src.services.auth_service import AuthService, User, Token
from src.models.schemas import ContextRequest, ContextResponse

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".env"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VibeCoding - Model Context Protocol Server",
    description="An MCP server for sales teams with integrations for Zoom, Gmail, and Notion",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create services
context_service = ContextService()
vector_context_service = VectorContextService()
auth_service = AuthService()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Authentication endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_service.verify_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# MCP endpoint for context gathering with authentication
@app.post("/context", response_model=ContextResponse)
async def get_context(
    request: ContextRequest,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    try:
        # Check source permissions
        if request.sources:
            for source in request.sources:
                if not auth_service.check_permission(current_user, source):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"User does not have permission to access source: {source}"
                    )
        
        # Use vector context service if available
        use_vector = request.query is not None
        
        if use_vector:
            context_response = await vector_context_service.get_context(request)
        else:
            context_response = await context_service.get_context(request)
            
            # Add new context to vector index for future searches
            await vector_context_service.add_to_index(context_response.context_items)
            
        return context_response
    except Exception as e:
        logger.error(f"Error processing context request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Backward compatibility for raw JSON requests
@app.post("/raw-context")
async def get_raw_context(
    request: Request,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    try:
        body = await request.json()
        
        # Convert raw request to our schema
        context_request = ContextRequest(
            query=body.get("query"),
            time_range=body.get("time_range"),
            sources=body.get("sources"),
            limit=body.get("limit", 10),
            entity_focus=body.get("entity_focus")
        )
        
        # Check source permissions
        if context_request.sources:
            for source in context_request.sources:
                if not auth_service.check_permission(current_user, source):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"User does not have permission to access source: {source}"
                    )
        
        # Use vector context service if available
        use_vector = context_request.query is not None
        
        if use_vector:
            context_response = await vector_context_service.get_context(context_request)
        else:
            context_response = await context_service.get_context(context_request)
            
            # Add new context to vector index for future searches
            await vector_context_service.add_to_index(context_response.context_items)
        
        # Convert to dict for raw response
        return context_response.dict()
    except Exception as e:
        logger.error(f"Error processing raw context request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Public API version info
@app.get("/api/version")
async def get_version():
    return {
        "name": "VibeCoding MCP Server",
        "version": "0.1.0",
        "description": "Model Context Protocol server for sales teams"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting MCP server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=debug) 