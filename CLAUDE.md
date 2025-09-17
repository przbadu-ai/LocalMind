# Local Mind

## Project Overview
Building an open-source, offline-first desktop RAG (Retrieval-Augmented Generation) application inspired by hyperlink.nexa.ai. The goal is to create a fully local document intelligence tool with advanced citation and highlighting features.

## Core Architecture Decisions

### Technology Stack
- **Desktop Framework**: Tauri (Rust-based, lightweight)
- **Frontend**: React + TypeScript + Shadcn UI
- **Routing**: React Router DOM (HashRouter for file:// protocol)
- **State Management**: Zustand (lightweight, persistent)
- **Backend**: Python FastAPI (running as Tauri sidecar process)
- **Vector Database**: LanceDB (embedded, file-based, no server required)
- **Document Processing**: PyMuPDF (with position tracking)
- **Model Inference**: Nexa SDK (supports GGUF, MLX formats)

## Key Features to Implement

### Must-Have Features
1. **Fully Offline Operation** - No internet required
2. **Cross-Platform** - Windows, Linux, macOS support
3. **Document Support** - PDF, DOCX, MD, TXT, PPTX, PNG/JPEG
4. **Model Management** - LMStudio-like interface for downloading/managing models
5. **OpenAI-Compatible API** - Connect to local inference servers (Ollama, vLLM, llamacpp)

### Killer Features (Unique Differentiators)
1. **Clickable Citations** - Each response paragraph links to source documents
2. **Exact Position Highlighting** - Click/hover on response opens document at exact location
3. **Smart Document Navigation** - Auto-scroll to relevant page and highlight source text
4. **Position-Aware Chunking** - Preserves bbox coordinates through entire pipeline

## Technical Implementation Details

### Document Processing Pipeline
```python
# Position tracking structure
{
    "text": "chunk text",
    "page": 1,
    "bbox": {"x0": 100, "y0": 200, "x1": 300, "y1": 250},
    "document_id": "doc_123",
    "chunk_id": "chunk_456"
}
```

### LanceDB Choice Rationale
- Embedded database (no server process)
- 40-60ms query latency
- 50MB memory footprint
- Native support for position metadata
- Simple file-based storage

### Frontend Architecture
- Allotment for VS Code-style split panes
- PDFSlick for document viewing
- Custom highlight overlay system
- React Router DOM with HashRouter
- Zustand for state management

## Project Structure
```
illuminate/
├── src/                    # React frontend
│   ├── components/
│   ├── stores/            # Zustand stores
│   └── views/
├── src-tauri/             # Tauri backend
├── backend/               # Python FastAPI
│   ├── main.py
│   ├── vector_store.py
│   └── document_processor.py
└── data/
    └── lancedb/          # Vector storage
```

## Development Priorities

### Phase 1 (MVP)
- [ ] Basic document ingestion (PDF, TXT, MD)
- [ ] Simple RAG pipeline with LanceDB
- [ ] Basic search interface
- [ ] Tauri shell with React frontend
- [ ] FastAPI backend integration

### Phase 2 (Killer Features)
- [ ] Position tracking in PyMuPDF
- [ ] Clickable citations implementation
- [ ] Document highlighting system
- [ ] Model management UI
- [ ] Multiple embedding models support

### Phase 3 (Polish)
- [ ] Performance optimization
- [ ] Advanced chunking strategies
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Open source release

## Naming Decision
**App Name**: To be decided (considering: Illuminate, DocuMind, Nexus, Beacon)

## Key Design Principles
1. **Privacy First** - Everything runs locally
2. **Performance** - Lightweight, fast queries (<100ms)
3. **User Experience** - Seamless document navigation
4. **Developer Friendly** - Clean architecture, easy to contribute
5. **Extensible** - Plugin architecture for future features

## Technical Challenges to Solve
1. Preserving exact text positions through chunking pipeline
2. Synchronizing highlights between frontend and backend
3. Efficient handling of large document collections
4. Real-time streaming responses with citations
5. Managing multiple model inference backends

## Repository Structure Goals
- Apache 2.0 License
- Comprehensive documentation
- GitHub Actions for multi-platform builds
- Community contribution guidelines
- Plugin system for extensions

## Performance Targets
- Bundle size: <10MB (Tauri advantage)
- Memory usage: <100MB idle
- Query response: <100ms
- Document indexing: <5 seconds per PDF
- Startup time: <1 second

## Notes
- User is a Full-Stack Rails/React engineer with ML/AI experience
- Preference for open-source, privacy-focused solutions
- Building for community contribution, not proprietary development