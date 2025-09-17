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

- Node.js 18+ or [Bun](https://bun.sh/) (recommended)
- Rust and Cargo (for Tauri)
- Python 3.8+ (for backend services)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/local-mind.git
cd local-mind
```

2. Install dependencies:
```bash
# Using Bun (recommended)
bun install

# Or using npm
npm install
```

3. Install Python dependencies (backend):
```bash
cd backend
pip install -r requirements.txt
cd ..
```

### Development

Run the application in development mode:

```bash
# Start Tauri development server
bun tauri dev

# Or with npm
npm run tauri dev
```

### Building

Build the application for production:

```bash
# Build for current platform
bun tauri build

# Or with npm
npm run tauri build
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
├── backend/               # Python FastAPI server
│   ├── main.py
│   ├── vector_store.py
│   └── document_processor.py
└── data/
    └── lancedb/          # Vector storage
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