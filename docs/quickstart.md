# VibeCoding MCP Server - Quick Start Guide

This guide will help you get started with using the VibeCoding MCP (Model Context Protocol) server to enhance your sales AI tools with contextual intelligence.

## Authentication

First, you need to obtain an access token:

```bash
# Request a token
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=sales&password=sales123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Save this token for use in subsequent requests.

## Basic Context Request

To retrieve context for a sales conversation:

```bash
# Get context related to a specific query
curl -X POST "http://localhost:8000/context" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "query": "customer concerns about pricing",
    "sources": ["zoom", "gmail", "notion"],
    "limit": 5
  }'
```

Response:
```json
{
  "source": "vibecoding-mcp-vector",
  "context_items": [
    {
      "type": "email",
      "source": "gmail",
      "content": "...",
      "subject": "Pricing Discussion",
      "sender": "customer@example.com",
      "recipients": ["sales@yourcompany.com"],
      "date": "2023-04-15T14:30:00",
      "thread_id": "thread123"
    },
    {
      "type": "meeting",
      "source": "zoom",
      "content": "...",
      "title": "Q1 Pricing Review",
      "participants": ["John Doe", "Jane Smith"],
      "date": "2023-04-10T10:00:00",
      "duration": 45,
      "meeting_id": "meeting456"
    }
    // Additional items...
  ],
  "query": "customer concerns about pricing",
  "timestamp": "2023-04-20T09:45:32"
}
```

## Advanced Features

### Entity-Focused Context

To get context about a specific account:

```bash
curl -X POST "http://localhost:8000/context" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "sources": ["salesforce"],
    "entity_focus": {
      "account_id": "0012t00000abcDEF"
    }
  }'
```

### Combining Multiple Sources

To get a comprehensive view of all interactions:

```bash
curl -X POST "http://localhost:8000/context" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "query": "annual contract renewal",
    "sources": ["zoom", "gmail", "notion", "salesforce"],
    "time_range": {
      "days_back": 90,
      "include_fresh": true
    }
  }'
```

## Integration with AI Assistants

You can use this MCP server as a context provider for AI assistants. Here's a Python example:

```python
import requests
import os
import json
from openai import OpenAI

# Get an access token
def get_token():
    response = requests.post(
        "http://localhost:8000/token",
        data={
            "username": "sales",
            "password": "sales123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]

# Get context from MCP server
def get_context(query, token):
    response = requests.post(
        "http://localhost:8000/context",
        json={
            "query": query,
            "sources": ["zoom", "gmail", "notion", "salesforce"],
            "limit": 10
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    return response.json()

# Use with OpenAI for contextual answers
def get_ai_response(query, context_items):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # Format context for the AI
    formatted_context = ""
    for item in context_items:
        formatted_context += f"\n\nSource: {item['source']} ({item['type']})\n"
        if item['type'] == 'email':
            formatted_context += f"Subject: {item['subject']}\nFrom: {item['sender']}\n"
        elif item['type'] == 'meeting':
            formatted_context += f"Title: {item['title']}\nDate: {item['date']}\n"
        formatted_context += f"Content: {item['content']}"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful sales assistant with access to context from various sources."},
            {"role": "user", "content": f"Based on the following context, {query}\n\nCONTEXT:\n{formatted_context}"}
        ]
    )
    
    return response.choices[0].message.content

# Main flow
def answer_sales_question(question):
    token = get_token()
    context = get_context(question, token)
    return get_ai_response(question, context["context_items"])

# Example usage
response = answer_sales_question("What were the main objections in our last meeting with Acme Corp?")
print(response)
```

## Next Steps

- Read the full [API Documentation](./api-docs.md)
- Learn about [Authentication and Security](./security.md)
- Check out [Deployment Options](./deployment.md) 