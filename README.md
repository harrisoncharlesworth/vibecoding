# VibeCoding - Model Context Protocol Server

A powerful Model Context Protocol (MCP) server implementation designed for sales teams to enhance their workflow by integrating with key sales tools. This server provides a unified API for retrieving contextual information from various data sources, enabling AI-powered sales assistance tools to access relevant customer interactions, communications, and data.

## 🌟 Features

### Core Functionality
- **MCP Server Implementation**: RESTful API following the Model Context Protocol
- **Vector-based Semantic Search**: Advanced context retrieval using embeddings
- **JWT Authentication**: Secure API access with role-based permissions
- **Real-time Context Gathering**: Dynamic aggregation of data from multiple sources

### Integrated Data Sources
- **Zoom Integration**
  - Meeting transcripts and recordings
  - Participant information
  - Meeting metadata and summaries

- **Gmail Integration**
  - Email content and threads
  - Attachment handling
  - Contact information

- **Notion Integration**
  - Knowledge base access
  - Document content and metadata
  - Page hierarchies and relationships

- **Salesforce Integration**
  - Account and contact information
  - Opportunity tracking
  - Customer interaction history

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker (optional)
- API credentials for integrated services

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vibecoding.git
cd vibecoding
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp config/.env.example config/.env
# Edit .env with your API credentials
```

4. Run the server:
```bash
python src/main.py
```

### Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

## 🔌 API Usage

### Authentication

Get an access token:
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=sales&password=sales123"
```

### Basic Context Query

Retrieve context based on a query:
```bash
curl -X POST "http://localhost:8000/context" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "customer pricing concerns",
    "sources": ["zoom", "gmail", "notion"],
    "limit": 5
  }'
```

### Advanced Queries

Entity-focused context:
```bash
curl -X POST "http://localhost:8000/context" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "sources": ["salesforce"],
    "entity_focus": {
      "account_id": "0012t00000abcDEF"
    }
  }'
```

Multi-source time-range query:
```bash
curl -X POST "http://localhost:8000/context" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "contract renewal",
    "sources": ["zoom", "gmail", "notion", "salesforce"],
    "time_range": {
      "days_back": 90,
      "include_fresh": true
    }
  }'
```

## 🔧 Configuration

### Environment Variables

Required environment variables in `.env`:
```env
# Server Configuration
PORT=8000
HOST=0.0.0.0
DEBUG=True
SECRET_KEY=your_secret_key_here

# API Keys
OPENAI_API_KEY=your_openai_api_key
ZOOM_CLIENT_ID=your_zoom_client_id
GMAIL_CLIENT_ID=your_gmail_client_id
NOTION_API_KEY=your_notion_api_key
SALESFORCE_CLIENT_ID=your_salesforce_client_id
# ... (see .env.example for full list)
```

### Authentication Configuration

Default user roles:
- `admin`: Full access to all sources
- `sales`: Configurable access to specific sources

## 🏗️ Project Structure

```
vibecoding/
├── src/
│   ├── integrations/     # API clients for external services
│   ├── models/          # Data models and schemas
│   ├── services/        # Core business logic
│   └── main.py         # FastAPI application
├── config/             # Configuration files
├── data/              # Vector store and persistent data
├── tests/             # Test suite
├── k8s/               # Kubernetes deployment files
└── docs/              # Documentation
```

## 🔐 Security

- JWT-based authentication
- Role-based access control
- API key encryption
- Rate limiting (configurable)
- CORS protection

## 🚢 Deployment

### Docker
```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes
```bash
# Apply configurations
kubectl apply -f k8s/

# Scale deployment
kubectl scale deployment mcp-server --replicas=5
```

## 🔍 Monitoring and Logging

- Health check endpoint: `/health`
- Structured logging with levels
- Metrics endpoint: `/metrics`
- Error tracking and reporting

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=src tests/
```

## 🛠️ Development

### Adding New Data Sources

1. Create integration client in `src/integrations/`
2. Define data models in `src/models/schemas.py`
3. Add service implementation in `src/services/`
4. Update context service to include new source

### Vector Store Management

- Location: `data/chroma/`
- Automatic indexing of new content
- Periodic reindexing for optimization
- Configurable chunk size and overlap

## 📚 Documentation

- [API Documentation](docs/api-docs.md)
- [Authentication Guide](docs/security.md)
- [Deployment Options](docs/deployment.md)
- [Integration Guide](docs/integration.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for embeddings support
- FastAPI framework
- LangChain for vector store implementation
- All integrated service providers

## 📞 Support

- Create an issue for bug reports
- Join our Discord community
- Email: support@vibecoding.com

## 🗺️ Roadmap

- [ ] Additional data source integrations
- [ ] Enhanced semantic search capabilities
- [ ] Real-time collaboration features
- [ ] Advanced analytics dashboard
- [ ] Custom plugin system