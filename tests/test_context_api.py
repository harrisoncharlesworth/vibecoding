import pytest
import json
from fastapi.testclient import TestClient
from datetime import datetime

from src.main import app
from src.models.schemas import ContextRequest

# Create test client
client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_context_endpoint():
    """Test the context endpoint with a simple request"""
    
    # Create a test request
    request_data = {
        "query": "sales proposal",
        "time_range": {"days_back": 14},
        "sources": ["zoom", "gmail", "notion"],
        "limit": 5
    }
    
    # Make the request to the API
    response = client.post("/context", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    
    # Basic structure validation
    assert "source" in data
    assert data["source"] == "vibecoding-mcp"
    assert "context_items" in data
    assert isinstance(data["context_items"], list)
    assert "query" in data
    assert data["query"] == "sales proposal"
    assert "timestamp" in data

def test_raw_context_endpoint():
    """Test the raw context endpoint"""
    
    # Create a test request
    request_data = {
        "query": "customer meeting",
        "sources": ["zoom"],
        "limit": 3
    }
    
    # Make the request to the API
    response = client.post("/raw-context", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    
    # Basic structure validation
    assert "source" in data
    assert data["source"] == "vibecoding-mcp"
    assert "context_items" in data
    assert isinstance(data["context_items"], list)
    assert "query" in data
    assert data["query"] == "customer meeting"

# Note: These tests are basic structure tests and would fail in a real environment
# because the integration clients would need mock data or real credentials 