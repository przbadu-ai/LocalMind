# Local Mind

A privacy-focused, offline-first AI chat application with YouTube video analysis, smart transcription, and LLM-powered conversations - all running locally on your machine.

![Local Mind Screenshot](docs/screenshot.png)

## What is Local Mind?

Local Mind is a desktop application that lets you:

1. **Chat with AI** - Have conversations with local LLMs (Ollama, LlamaCpp, etc.) or cloud providers (OpenAI)
2. **Analyze YouTube Videos** - Paste a YouTube URL and get intelligent summaries, Q&A, and insights from video transcripts
3. **Keep Everything Local** - Your data stays on your machine. No cloud dependencies required.

## Key Features

### AI Chat
- **Streaming Responses** - Real-time token-by-token response streaming
- **LLM-Generated Titles** - Chat titles are automatically generated based on conversation content
- **Thinking Process Display** - Collapsible "Thinking" blocks show LLM reasoning when applicable
- **Markdown Rendering** - Full markdown support with code highlighting, tables, and more
- **Chat History** - All conversations are saved locally in SQLite

### YouTube Integration
- **Automatic Transcript Extraction** - Just paste a YouTube URL to extract the full transcript
- **Smart Summarization** - Get structured summaries with key points, not raw transcript dumps
- **Interactive Timestamps** - Click timestamps in the transcript to seek the video
- **Side-by-Side View** - Watch the video while reading the transcript and chatting
- **Grouped Segments** - Transcripts are grouped into 10-60 second chunks for better readability

### Privacy & Flexibility
- **Offline-First** - Works with local LLM servers, no internet required for chat
- **Multiple LLM Providers** - Supports Ollama, LlamaCpp, vLLM, OpenAI, and any OpenAI-compatible API
- **Configure via Settings** - Change LLM provider, model, and API URL from the app's Settings page
- **Network Access** - Access the app from mobile devices or other PCs on your network

### MCP (Model Context Protocol) Support
- **Add MCP Servers** - Configure external MCP servers for extended capabilities
- **Tool Integration** - Use tools provided by MCP servers in your conversations

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Desktop** | Tauri (Rust) |
| **Frontend** | React 19 + TypeScript + Vite |
| **UI** | Shadcn UI + Tailwind CSS |
| **State** | Zustand |
| **Backend** | Python FastAPI |
| **AI Agents** | Pydantic AI |
| **Database** | SQLite |

## Getting Started

### Prerequisites

- **[Bun](https://bun.sh/)** - JavaScript runtime and package manager
- **[Rust](https://www.rust-lang.org/tools/install)** - Required for Tauri (latest stable)
- **Python 3.11+** - Backend runtime
- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
- **LLM Server** - [Ollama](https://ollama.ai/), LlamaCpp, or any OpenAI-compatible endpoint

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/LocalMind.git
cd LocalMind

# 2. Install frontend dependencies
bun install

# 3. Setup Python backend
cd backend
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
cd ..

# 4. Start your LLM server (example with Ollama)
ollama pull llama3:instruct
ollama serve  # Runs on http://localhost:11434

# 5. Run the app (starts both frontend and backend)
bun tauri:dev
```

The app will be available at:
- **Desktop**: Tauri window opens automatically
- **Browser**: http://localhost:1420
- **Network**: http://your-ip:1420 (accessible from mobile/other PCs)

### Configure LLM Settings

1. Open the app and go to **Settings** (gear icon in sidebar)
2. Configure your LLM provider:
   - **Provider**: Ollama, LlamaCpp, or OpenAI
   - **Base URL**: e.g., `http://localhost:11434/v1` for Ollama
   - **Model**: e.g., `llama3:instruct`
3. Click **Test Connection** to verify
4. Click **Save Settings**

## Usage

### Basic Chat

1. Click **+ New Chat** in the sidebar
2. Type your message and press Enter
3. The AI will respond with streaming text

### YouTube Video Analysis

1. Start a new chat or use an existing one
2. Paste a YouTube URL: `https://www.youtube.com/watch?v=VIDEO_ID`
3. Local Mind will:
   - Extract the video transcript
   - Display the video player and transcript side-by-side
   - Generate a structured summary with key points
4. Ask follow-up questions about the video content!

### Tips

- **Click timestamps** in the transcript to jump to that point in the video
- **Expand "Thinking" blocks** to see the LLM's reasoning process
- **Pin important chats** by clicking the pin icon (keeps them at the top)
- **Access from mobile** - The app is accessible on your local network

## Development

### Running Individual Components

```bash
# Frontend only (React dev server)
bun dev

# Backend only
cd backend && source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 52817 --reload

# Full Tauri app
bun tauri:dev
```

### API Documentation

When the backend is running, visit:
- **Swagger UI**: http://localhost:52817/docs
- **ReDoc**: http://localhost:52817/redoc

### Project Structure

```
LocalMind/
├── src/                    # React frontend
│   ├── components/         # UI components
│   │   ├── ui/             # Shadcn components
│   │   ├── youtube/        # Video player & transcript
│   │   └── MarkdownRenderer.tsx  # Markdown with thinking blocks
│   ├── pages/              # Route pages
│   │   ├── ChatDetails.tsx # Main chat interface
│   │   └── Settings.tsx    # LLM & MCP configuration
│   ├── services/           # API clients
│   └── stores/             # Zustand state
├── src-tauri/              # Tauri (Rust) desktop shell
├── backend/                # Python FastAPI
│   ├── agents/             # Pydantic AI agents
│   │   ├── chat_agent.py   # Chat functionality
│   │   ├── youtube_agent.py # Video analysis
│   │   └── title_agent.py  # LLM title generation
│   ├── api/                # REST endpoints
│   ├── database/           # SQLite with repositories
│   └── services/           # Business logic
├── app.config.json         # Shared configuration
└── data/                   # SQLite database & cache
```

## Configuration

### app.config.json

The main configuration file for both frontend and backend:

```json
{
  "backend": {
    "host": "0.0.0.0",
    "port": 52817,
    "api_base_url": "http://127.0.0.1:52817"
  },
  "models": {
    "llm": {
      "provider": "ollama",
      "default_model": "llama3:instruct",
      "ollama": {
        "base_url": "http://localhost:11434"
      }
    }
  },
  "features": {
    "enable_youtube": true,
    "enable_mcp": true
  }
}
```

### Environment Variables

LLM settings are managed via the Settings page, but you can also use environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_HOST` | Server bind address | `0.0.0.0` |
| `BACKEND_PORT` | Server port | `52817` |
| `DATABASE_PATH` | SQLite database path | `./data/local_mind.db` |

## Building for Production

```bash
# Build the Tauri desktop app
bun tauri build
```

Output will be in `src-tauri/target/release/`:
- **Linux**: `.deb`, `.AppImage`
- **macOS**: `.dmg`, `.app`
- **Windows**: `.msi`, `.exe`

## Troubleshooting

### LLM Connection Issues

```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check the OpenAI-compatible endpoint
curl http://localhost:11434/v1/models
```

### Port Already in Use

```bash
# Kill processes on the ports
lsof -ti :52817 | xargs kill -9  # Backend
lsof -ti :1420 | xargs kill -9   # Frontend
```

### YouTube Transcript Not Loading

Some videos don't have transcripts available. The app will show an error message with helpful suggestions if extraction fails.

## Roadmap

- [ ] Document upload and RAG (PDF, DOCX, etc.)
- [ ] Voice input/output
- [ ] Image analysis with vision models
- [ ] Plugin system for extensions
- [ ] Export conversations to markdown

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

Apache 2.0 License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Tauri](https://tauri.app/) - Lightweight desktop framework
- [Shadcn UI](https://ui.shadcn.com/) - Beautiful UI components
- [Pydantic AI](https://ai.pydantic.dev/) - AI agent framework
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) - YouTube transcript extraction
- [Ollama](https://ollama.ai/) - Local LLM server
