# Local Mind Backend

A modular FastAPI backend for the Local Mind RAG application.

## Architecture

```
backend/
├── api/               # API route handlers
│   ├── chat.py       # Chat endpoints
│   ├── documents.py  # Document management
│   ├── health.py     # Health checks
│   └── search.py     # Search endpoints
├── config/           # Configuration management
│   └── settings.py   # App settings
├── core/             # Core functionality
│   ├── exceptions.py # Custom exceptions
│   └── middleware.py # Middleware setup
├── models/           # Pydantic models
│   └── schemas.py    # Request/response schemas
├── services/         # Business logic
│   ├── chat_service.py     # Chat & RAG pipeline
│   ├── document_service.py # Document processing
│   └── vector_service.py   # Vector store operations
└── main.py          # FastAPI application
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env as needed
```

### 3. Run Development Server

```bash
# Option 1: Using the script
./run_dev.sh

# Option 2: Manual
python main.py
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

### 4. Test the API

```bash
python test_api.py
```

## API Endpoints

### Health & Info
- `GET /api/v1/health` - Health check
- `GET /api/v1/ping` - Simple ping
- `GET /api/v1/info` - API information

### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/` - List all documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document
- `POST /api/v1/documents/{id}/reprocess` - Reprocess document

### Chat
- `POST /api/v1/chat/` - Send chat message
- `GET /api/v1/chat/conversations/{id}/history` - Get conversation history
- `DELETE /api/v1/chat/conversations/{id}` - Clear conversation

### Search
- `POST /api/v1/search/` - Semantic search
- `GET /api/v1/search/` - Search (GET method)
- `GET /api/v1/search/stats` - Vector store statistics

## Features

✅ **Modular Architecture** - Clean separation of concerns
✅ **FastAPI** - Modern, fast web framework
✅ **Async Support** - Fully async/await compatible
✅ **Type Safety** - Pydantic models for validation
✅ **CORS Ready** - Configured for Tauri integration
✅ **Error Handling** - Comprehensive exception handling
✅ **API Documentation** - Auto-generated OpenAPI docs
✅ **Vector Search** - LanceDB integration
✅ **Document Processing** - Multi-format support
✅ **RAG Pipeline** - Context-aware responses

## Integration with Frontend

The backend is designed to work with the Tauri frontend:

1. CORS is configured for `tauri://localhost`
2. API responses include proper headers
3. File uploads support multipart/form-data
4. Real-time streaming ready (for future implementation)

## Development

### Adding New Endpoints

1. Create route handler in `api/`
2. Define schemas in `models/schemas.py`
3. Implement business logic in `services/`
4. Register router in `api/__init__.py`

### Testing

```bash
# Run API tests
python test_api.py

# Test with curl
curl http://localhost:8000/api/v1/health

# Upload a document
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"
```

## Next Steps

- [ ] Implement PyMuPDF document processor
- [ ] Add real LLM integration (Ollama/OpenAI)
- [ ] Implement streaming responses
- [ ] Add authentication/authorization
- [ ] Set up database for persistent storage
- [ ] Add comprehensive logging
- [ ] Create unit tests
- [ ] Add performance monitoring