# Local Mind

An open-source, offline-first desktop RAG (Retrieval-Augmented Generation) application that provides intelligent document analysis with advanced citation and highlighting features - all running completely locally on your machine.

## 🎯 Overview

Local Mind is a privacy-focused desktop application that brings AI-powered document intelligence to your local machine. Inspired by tools like hyperlink.nexa.ai, it offers advanced RAG capabilities without requiring an internet connection or sending your data to external servers.

### Key Features

- **🔒 Fully Offline Operation** - No internet required, your data never leaves your machine
- **🖥️ Cross-Platform** - Works on Windows, Linux, and macOS
- **📄 Multi-Format Support** - PDF, DOCX, MD, TXT, PPTX, PNG/JPEG
- **🤖 Local AI Models** - Support for GGUF, MLX formats via Nexa SDK
- **🔗 OpenAI-Compatible API** - Connect to local inference servers (Ollama, vLLM, llamacpp)
- **📍 Clickable Citations** - Each response paragraph links directly to source documents
- **✨ Smart Highlighting** - Click/hover on responses to see exact source location in documents

## 🚀 Getting Started

### Prerequisites

- **Node.js 18+** or **[Bun](https://bun.sh/)** (recommended for faster performance)
- **[Rust](https://www.rust-lang.org/tools/install)** (latest stable)
- **Python 3.8+** with pip
- **Git**
- **[Ollama](https://ollama.ai/)** (optional, for local LLM inference)

## 📦 Development Setup

We provide two ways to set up your development environment: using **Bun** (recommended) or **npm**.

### Using Bun (Recommended) 🚀

Bun is a fast JavaScript runtime that significantly speeds up development.

#### 1. Install Bun

```bash
# macOS/Linux
curl -fsSL https://bun.sh/install | bash

# Windows (PowerShell)
powershell -c "irm bun.sh/install.ps1|iex"
```

#### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/local-mind.git
cd local-mind

# Install frontend dependencies
bun install

# Setup Python backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

#### 3. Run Development Server

```bash
# Start both frontend and backend with one command
bun tauri:dev

# Or run them separately:
bun dev:frontend  # Frontend only
bun dev:backend   # Backend only
```

#### 4. Build for Production

```bash
# Build everything (frontend + backend + desktop app)
bun tauri:build
```

### Using npm 📦

If you prefer using npm, here's the traditional setup:

#### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/local-mind.git
cd local-mind

# Install frontend dependencies
npm install

# Setup Python backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

#### 2. Run Development Server

```bash
# Start both frontend and backend
npm run tauri:dev

# Or run them separately:
npm run dev:frontend  # Frontend only
npm run dev:backend   # Backend only
```

#### 3. Build for Production

```bash
# Build everything (frontend + backend + desktop app)
npm run tauri:build
```

## 🛠️ Available Scripts

### Development Commands

| Command | Bun | npm | Description |
|---------|-----|-----|-------------|
| Dev (All) | `bun tauri:dev` | `npm run tauri:dev` | Start frontend + backend + Tauri |
| Frontend Only | `bun dev:frontend` | `npm run dev:frontend` | Start Vite dev server |
| Backend Only | `bun dev:backend` | `npm run dev:backend` | Start Python FastAPI server |
| Build All | `bun tauri:build` | `npm run tauri:build` | Build production app |
| Build Frontend | `bun build:frontend` | `npm run build:frontend` | Build frontend only |
| Build Backend | `bun build:backend` | `npm run build:backend` | Bundle Python backend |

### Quick Start Commands

```bash
# 🚀 Development (everything runs with one command!)
bun tauri:dev  # or: npm run tauri:dev

# 📦 Production Build
bun tauri:build  # or: npm run tauri:build
```

## 🏗️ Tech Stack

### Frontend
- **Framework**: React + TypeScript
- **UI Components**: Shadcn UI with Radix UI primitives
- **Styling**: Tailwind CSS v3
- **State Management**: Zustand
- **Routing**: React Router DOM (HashRouter)

### Backend
- **Desktop Framework**: Tauri (Rust)
- **API Server**: Python FastAPI (sidecar process)
- **Vector Database**: LanceDB (embedded, file-based)
- **Document Processing**: PyMuPDF
- **Model Inference**: Nexa SDK

### Build Tools
- **Bundler**: Vite
- **Package Manager**: Bun/npm
- **Type Checking**: TypeScript

## 📁 Project Structure

```
local-mind/
├── src/                    # React frontend
│   ├── components/         # UI components
│   │   ├── ui/            # Shadcn UI components
│   │   └── ...            # App-specific components
│   ├── pages/             # Route pages
│   ├── hooks/             # Custom React hooks
│   └── lib/               # Utilities
├── src-tauri/             # Tauri backend (Rust)
│   ├── src/               # Rust source code
│   └── tauri.conf.json   # Tauri configuration
├── backend/               # Python FastAPI server
│   ├── api/               # API endpoints
│   ├── config/            # Configuration management
│   ├── core/              # Core functionality
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   └── main.py           # FastAPI entry point
├── bin/                   # Executable scripts
│   ├── dev.sh            # Unix dev starter
│   ├── dev.bat           # Windows dev starter
│   ├── start_backend.sh  # Backend startup script
│   ├── start_backend.bat # Backend startup (Windows)
│   └── run_dev.sh        # Direct backend runner
└── data/                  # Application data (auto-created)
    ├── lancedb/          # Vector storage
    └── uploads/          # Uploaded documents

## ⚙️ Configuration

### Backend API

The backend server runs on `http://localhost:8000` by default. API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### LLM Setup (Ollama)

1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull a model:
```bash
ollama pull llama2  # or any other model
```
3. The app will automatically detect and use Ollama

### Application Settings

Settings are stored in platform-specific locations:
- **Windows**: `%APPDATA%\LocalMind\config.json`
- **macOS**: `~/Library/Application Support/LocalMind/config.json`
- **Linux**: `~/.config/LocalMind/config.json`

## 🐛 Troubleshooting

### Common Issues

**Backend not starting:**
```bash
# Check Python version (needs 3.8+)
python --version

# Reinstall dependencies
cd backend
pip install -r requirements.txt
```

**Tauri build fails:**
```bash
# Update Rust
rustup update

# Clean and rebuild
cargo clean
bun tauri build
```

**Port already in use:**
```bash
# Kill process on port 8000 (backend)
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines

- Follow the existing code style and conventions
- Write clear, descriptive commit messages
- Add tests for new features when applicable
- Update documentation as needed
- Be respectful and constructive in discussions

### Areas for Contribution

- 🐛 Bug fixes and issue resolution
- ✨ New features and enhancements
- 📚 Documentation improvements
- 🎨 UI/UX improvements
- 🚀 Performance optimizations
- 🧪 Test coverage expansion
- 🌍 Internationalization

## 🗺️ Roadmap

### Phase 1 (MVP) - Current
- ✅ Basic document ingestion (PDF, TXT, MD)
- ✅ Tauri shell with React frontend
- ⬜ Simple RAG pipeline with LanceDB
- ⬜ Basic search interface
- ⬜ FastAPI backend integration

### Phase 2 (Killer Features)
- ⬜ Position tracking in PyMuPDF
- ⬜ Clickable citations implementation
- ⬜ Document highlighting system
- ⬜ Model management UI
- ⬜ Multiple embedding models support

### Phase 3 (Polish)
- ⬜ Performance optimization
- ⬜ Advanced chunking strategies
- ⬜ Comprehensive testing
- ⬜ Plugin architecture
- ⬜ Public release

## 📝 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [hyperlink.nexa.ai](https://hyperlink.nexa.ai)
- Built with [Tauri](https://tauri.app/)
- UI components from [Shadcn UI](https://ui.shadcn.com/)
- Vector database by [LanceDB](https://lancedb.com/)

## 📧 Contact

For questions, suggestions, or discussions:
- Open an issue on GitHub
- Join our Discord community (coming soon)
- Email: your-email@example.com

## ⚡ Performance Targets

- Bundle size: <10MB (Tauri advantage)
- Memory usage: <100MB idle
- Query response: <100ms
- Document indexing: <5 seconds per PDF
- Startup time: <1 second

---

**Note**: This project is under active development. Features and APIs may change.

Built with ❤️ for the open-source community