# LocalMind Architecture

## Overview

LocalMind is a desktop AI chat application built with a three-tier architecture:

1. **Frontend** - React/TypeScript with Tauri desktop wrapper
2. **Backend** - Python FastAPI with Pydantic AI agents
3. **Storage** - SQLite database for persistence

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Application                       │
│                     (Tauri + React)                          │
├─────────────────────────────────────────────────────────────┤
│                        HTTP/SSE                              │
├─────────────────────────────────────────────────────────────┤
│                    Python FastAPI                            │
│              (Pydantic AI Agents + Services)                 │
├─────────────┬─────────────────────┬─────────────────────────┤
│   Chat API  │    YouTube API      │     MCP API             │
├─────────────┴─────────────────────┴─────────────────────────┤
│                     SQLite Database                          │
│           (Chats, Messages, Transcripts, Config)             │
└─────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

### Technology Stack

- **Framework**: React 18 with TypeScript
- **Desktop**: Tauri (Rust-based, lightweight)
- **UI Components**: Shadcn UI + Radix UI primitives
- **Styling**: Tailwind CSS
- **State Management**: Zustand with persistence
- **Routing**: React Router DOM (HashRouter)

### Directory Structure

```
src/
├── components/
│   ├── ui/                    # Shadcn UI components
│   ├── youtube/               # YouTube player & transcript
│   │   ├── YouTubePlayer.tsx  # Embedded player with JS API
│   │   └── TranscriptViewer.tsx # Clickable timestamps
│   ├── app-sidebar.tsx        # Navigation sidebar
│   └── app-header.tsx         # Header with title
├── pages/
│   ├── ChatDetails.tsx        # Main chat interface
│   ├── Chats.tsx              # Chat list
│   └── Settings.tsx           # LLM & MCP configuration
├── services/
│   ├── chat-service.ts        # Chat API client
│   ├── youtube-service.ts     # YouTube API client
│   ├── mcp-service.ts         # MCP API client
│   └── settings-service.ts    # Settings API client
├── stores/
│   ├── useChatStore.ts        # Chat state with video context
│   ├── useSettingsStore.ts    # Settings state
│   └── useHeaderStore.ts      # Header title state
└── config/
    └── app-config.ts          # Centralized configuration
```

### State Management

Zustand stores handle application state:

```typescript
// Chat Store - manages current chat and video context
interface ChatState {
  currentChat: Chat | null;
  messages: Message[];
  videoContext: VideoContext | null;
  isStreaming: boolean;
}

// Settings Store - manages LLM and MCP configuration
interface SettingsState {
  llmConfig: LLMConfig | null;
  mcpServers: MCPServer[];
  isLLMConnected: boolean;
}
```

### Two-Column Layout

When a YouTube video is detected, the chat interface switches to a two-column layout:

```
┌──────────────────┬───────────────────────────────┐
│                  │                               │
│    Chat Panel    │      Video + Transcript       │
│    (Messages)    │                               │
│                  │  ┌─────────────────────────┐  │
│                  │  │    YouTube Player       │  │
│                  │  └─────────────────────────┘  │
│                  │  ┌─────────────────────────┐  │
│                  │  │    Transcript Viewer    │  │
│                  │  │    (Clickable times)    │  │
│                  │  └─────────────────────────┘  │
└──────────────────┴───────────────────────────────┘
```

## Backend Architecture

### Technology Stack

- **Framework**: FastAPI with async support
- **AI Agents**: Pydantic AI with tool support
- **Database**: SQLite with aiosqlite
- **LLM Client**: OpenAI SDK (compatible with Ollama, LlamaCpp)
- **YouTube**: youtube-transcript-api

### Directory Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── config.py                  # Pydantic Settings from .env
├── agents/
│   ├── chat_agent.py          # Main chat agent with tools
│   └── youtube_agent.py       # Video summarization/Q&A
├── api/
│   ├── chat.py                # SSE streaming chat endpoint
│   ├── chats.py               # Chat CRUD endpoints
│   ├── youtube.py             # YouTube transcript endpoints
│   ├── mcp.py                 # MCP server management
│   └── settings.py            # Settings/config endpoints
├── database/
│   ├── connection.py          # SQLite connection & schema
│   ├── models.py              # Pydantic models
│   └── repositories/          # Data access layer
│       ├── chat_repository.py
│       ├── message_repository.py
│       ├── transcript_repository.py
│       └── config_repository.py
├── services/
│   ├── llm_service.py         # OpenAI-compatible client
│   ├── youtube_service.py     # Transcript extraction
│   └── mcp_service.py         # MCP server lifecycle
└── utils/
    ├── youtube_utils.py       # URL parsing utilities
    └── timestamp_utils.py     # Timestamp formatting
```

### Pydantic AI Agents

The backend uses Pydantic AI agents for intelligent chat processing:

```python
# Chat Agent - detects YouTube URLs and provides context
@dataclass
class ChatDeps:
    transcript: Optional[Transcript]
    video_id: Optional[str]

agent = Agent(
    model=OpenAIModel(...),
    deps_type=ChatDeps,
    result_type=ChatResponse,
    system_prompt="...",
)

# Agent tools for YouTube detection
@agent.tool
def detect_youtube_url(ctx: RunContext[ChatDeps], message: str) -> dict:
    """Extract YouTube URLs from message."""
    ...

@agent.tool
def search_transcript(ctx: RunContext[ChatDeps], query: str) -> list:
    """Search transcript for matching content."""
    ...
```

### Database Schema

```sql
-- Chats table
CREATE TABLE chats (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    is_archived INTEGER DEFAULT 0,
    is_pinned INTEGER DEFAULT 0
);

-- Messages with artifact support
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    artifact_type TEXT,  -- 'youtube', 'pdf', 'image'
    artifact_data TEXT,  -- JSON blob
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);

-- YouTube transcript cache
CREATE TABLE transcripts (
    id TEXT PRIMARY KEY,
    video_id TEXT UNIQUE NOT NULL,
    video_url TEXT,
    language_code TEXT,
    is_generated INTEGER,
    segments TEXT,  -- JSON array
    full_text TEXT,
    created_at TEXT NOT NULL
);

-- MCP server configurations
CREATE TABLE mcp_servers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    server_type TEXT NOT NULL,  -- 'stdio' or 'sse'
    command TEXT,
    args TEXT,  -- JSON array
    url TEXT,
    env TEXT,  -- JSON object
    is_enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);
```

## API Design

### Chat Streaming (SSE)

The chat endpoint uses Server-Sent Events for real-time streaming:

```
POST /api/v1/chat/stream
Content-Type: application/json

{
  "message": "Summarize this video: https://youtube.com/watch?v=abc123",
  "conversation_id": "chat_123"
}

Response: text/event-stream

data: {"type": "youtube_detected", "video_id": "abc123", "url": "..."}
data: {"type": "transcript_status", "success": true}
data: {"type": "content", "content": "The video discusses..."}
data: {"type": "content", "content": " three main topics..."}
data: {"type": "done", "message_id": "msg_456"}
```

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chats` | GET | List recent chats |
| `/api/v1/chats` | POST | Create new chat |
| `/api/v1/chats/{id}` | GET | Get chat with messages |
| `/api/v1/chats/{id}` | DELETE | Delete chat |
| `/api/v1/youtube/transcript` | POST | Extract transcript |
| `/api/v1/youtube/transcript/{id}` | GET | Get cached transcript |
| `/api/v1/mcp/servers` | GET/POST | Manage MCP servers |
| `/api/v1/settings/llm` | GET/PUT | LLM configuration |

## Configuration System

### Centralized Configuration

Configuration is managed through multiple layers:

1. **app.config.json** - Static defaults for frontend/backend
2. **.env** - Environment-specific overrides (secrets, URLs)
3. **SQLite configurations table** - User runtime settings

```
┌─────────────────┐
│ app.config.json │ ← Static defaults (committed)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     .env        │ ← Environment overrides (not committed)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQLite config   │ ← User settings (runtime)
└─────────────────┘
```

### Configuration Flow

```python
# Backend loads settings with priority:
# 1. Environment variables (.env)
# 2. Defaults from code/app.config.json

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_provider: str = "ollama"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3:instruct"

    model_config = SettingsConfigDict(env_file=".env")
```

## Data Flow

### Chat with YouTube Detection

```
User sends message with YouTube URL
            │
            ▼
┌─────────────────────────┐
│   Frontend sends POST   │
│   /api/v1/chat/stream   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Chat Agent detects URL │
│  via detect_youtube_url │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  YouTube Service fetches│
│  transcript via API     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Cache transcript in    │
│  SQLite database        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Stream SSE events:     │
│  - youtube_detected     │
│  - transcript_status    │
│  - content (chunks)     │
│  - done                 │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Frontend updates:      │
│  - Shows video player   │
│  - Shows transcript     │
│  - Displays response    │
└─────────────────────────┘
```

## Security Considerations

### CORS Configuration

The backend allows specific origins for Tauri and development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",    # Dev server
        "tauri://localhost",         # Tauri app
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Key Handling

- LLM API keys stored in `.env` (not committed)
- Settings page masks API key input
- Keys never logged or exposed in responses

## Performance Considerations

### Streaming for Long Responses

SSE streaming prevents timeout issues with LLM responses:
- Immediate feedback to user
- No buffering of entire response
- Graceful error handling mid-stream

### Transcript Caching

YouTube transcripts are cached in SQLite:
- Avoids repeated API calls
- Fast retrieval for subsequent questions
- Manual cache clearing available

### Database Indexing

```sql
CREATE INDEX idx_messages_chat_id ON messages(chat_id);
CREATE INDEX idx_transcripts_video_id ON transcripts(video_id);
CREATE INDEX idx_chats_updated ON chats(updated_at);
```
