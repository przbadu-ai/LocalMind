# Local Mind

An AI chat application with YouTube transcription, MCP (Model Context Protocol) support, and OpenAI-compatible API integration - all running locally on your machine.

## Features

- **AI Chat** - Chat with LLMs using OpenAI-compatible APIs (Ollama, LlamaCpp, vLLM, OpenAI)
- **YouTube Transcription** - Extract and interact with YouTube video transcripts
- **Clickable Timestamps** - Click on timestamps in transcripts to seek video
- **MCP Server Support** - Connect to Model Context Protocol servers for extended capabilities
- **Offline-First** - Works with local LLM servers, no internet required
- **Cross-Platform** - Windows, Linux, and macOS support via Tauri

## Tech Stack

- **Frontend**: React + TypeScript + Shadcn UI + Tailwind CSS
- **Desktop**: Tauri (Rust)
- **Backend**: Python FastAPI with Pydantic AI agents
- **Database**: SQLite
- **State Management**: Zustand

## Prerequisites

- **[Bun](https://bun.sh/)** (recommended) or Node.js 18+
- **[Rust](https://www.rust-lang.org/tools/install)** (latest stable)
- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (Python package manager)
- **[Ollama](https://ollama.ai/)** (or other OpenAI-compatible LLM server)

## Quick Start

### 1. Install uv (Python Package Manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/LocalMind.git
cd LocalMind

# Install frontend dependencies
bun install

# Setup Python backend with uv
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
cd ..

# Copy environment file
cp .env.example .env
```

### 3. Configure Environment

Edit `.env` with your LLM settings:

```env
# LLM Configuration
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=not-required
LLM_MODEL=llama3:instruct

# Backend Server
BACKEND_HOST=127.0.0.1
BACKEND_PORT=52817

# Database
DATABASE_PATH=./data/local_mind.db
```

### 4. Start Ollama (or your LLM server)

```bash
# Install Ollama from https://ollama.ai/
# Pull a model
ollama pull llama3:instruct

# Ollama runs on http://localhost:11434 by default
```

### 5. Run the Application

```bash
# Terminal 1: Start the Python backend
cd backend
source .venv/bin/activate
uv run uvicorn main:app --host 127.0.0.1 --port 52817 --reload

# Terminal 2: Start the frontend (development)
bun dev

# Or for Tauri desktop app:
bun tauri dev
```

## Development

### Backend Only

```bash
cd backend
source .venv/bin/activate
uv run uvicorn main:app --host 127.0.0.1 --port 52817 --reload
```

The API will be available at:
- API: http://127.0.0.1:52817
- Swagger Docs: http://127.0.0.1:52817/docs
- ReDoc: http://127.0.0.1:52817/redoc

### Frontend Only

```bash
bun dev
```

Frontend runs at http://localhost:1420

### Full Tauri App

```bash
bun tauri dev
```

## Project Structure

```
LocalMind/
├── src/                          # React frontend
│   ├── components/               # UI components
│   │   ├── ui/                   # Shadcn UI components
│   │   └── youtube/              # YouTube player & transcript
│   ├── pages/                    # Route pages
│   ├── services/                 # API clients
│   └── stores/                   # Zustand state stores
├── src-tauri/                    # Tauri (Rust) backend
├── backend/                      # Python FastAPI backend
│   ├── agents/                   # Pydantic AI agents
│   │   ├── chat_agent.py         # Main chat agent
│   │   └── youtube_agent.py      # YouTube summarization/Q&A
│   ├── api/                      # FastAPI routes
│   │   ├── chat.py               # SSE streaming chat
│   │   ├── chats.py              # Chat CRUD
│   │   ├── youtube.py            # YouTube transcript
│   │   ├── mcp.py                # MCP server management
│   │   └── settings.py           # Settings/config
│   ├── database/                 # SQLite database layer
│   │   ├── connection.py         # DB connection & schema
│   │   ├── models.py             # Pydantic models
│   │   └── repositories/         # Data access layer
│   ├── services/                 # Business logic
│   │   ├── llm_service.py        # OpenAI-compatible client
│   │   ├── youtube_service.py    # Transcript extraction
│   │   └── mcp_service.py        # MCP server management
│   └── utils/                    # Utilities
├── data/                         # Application data
│   └── local_mind.db             # SQLite database
├── app.config.json               # App configuration
└── .env                          # Environment variables
```

## API Endpoints

### Chat
- `POST /api/v1/chat/stream` - Stream chat response (SSE)
- `GET /api/v1/chats` - List recent chats
- `POST /api/v1/chats` - Create new chat
- `GET /api/v1/chats/{id}` - Get chat with messages
- `DELETE /api/v1/chats/{id}` - Delete chat

### YouTube
- `POST /api/v1/youtube/transcript` - Extract transcript from URL
- `GET /api/v1/youtube/transcript/{video_id}` - Get cached transcript
- `GET /api/v1/youtube/languages/{video_id}` - Available languages

### MCP
- `GET /api/v1/mcp/servers` - List MCP servers
- `POST /api/v1/mcp/servers` - Add server
- `POST /api/v1/mcp/servers/{id}/start` - Start server
- `POST /api/v1/mcp/servers/{id}/stop` - Stop server
- `GET /api/v1/mcp/servers/{id}/tools` - List available tools

### Settings
- `GET /api/v1/settings/llm` - Get LLM configuration
- `PUT /api/v1/settings/llm` - Update LLM configuration
- `GET /api/v1/settings/llm/models` - List available models
- `GET /api/v1/settings/llm/health` - Check LLM connectivity

## Configuration

### app.config.json

Central configuration file for both frontend and backend:

```json
{
  "backend": {
    "host": "127.0.0.1",
    "port": 52817,
    "api_base_url": "http://127.0.0.1:52817"
  },
  "models": {
    "llm": {
      "provider": "ollama",
      "default_model": "llama3:instruct"
    }
  },
  "features": {
    "enable_youtube": true,
    "enable_mcp": true
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (ollama/openai/llamacpp) | `ollama` |
| `LLM_BASE_URL` | OpenAI-compatible API URL | `http://localhost:11434/v1` |
| `LLM_API_KEY` | API key (use "not-required" for local) | `not-required` |
| `LLM_MODEL` | Default model name | `llama3:instruct` |
| `BACKEND_HOST` | Backend server host | `127.0.0.1` |
| `BACKEND_PORT` | Backend server port | `52817` |
| `DATABASE_PATH` | SQLite database path | `./data/local_mind.db` |

## Building for Production

```bash
# Build Tauri desktop app
bun tauri build
```

The built application will be in `src-tauri/target/release/`.

## Troubleshooting

### Backend Issues

```bash
# Check Python version (needs 3.11+)
python --version

# Reinstall dependencies with uv
cd backend
uv pip install -r requirements.txt --force-reinstall

# Check if port is in use
lsof -i :52817  # Linux/macOS
netstat -ano | findstr :52817  # Windows
```

### LLM Connection Issues

```bash
# Test Ollama is running
curl http://localhost:11434/api/tags

# Test OpenAI-compatible endpoint
curl http://localhost:11434/v1/models
```

### Frontend Issues

```bash
# Clear cache and reinstall
rm -rf node_modules bun.lockb
bun install
```

## License

Apache 2.0 License - see [LICENSE](LICENSE) file.

## Acknowledgments

- [Tauri](https://tauri.app/) - Desktop framework
- [Shadcn UI](https://ui.shadcn.com/) - UI components
- [Pydantic AI](https://ai.pydantic.dev/) - AI agent framework
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) - YouTube transcripts
