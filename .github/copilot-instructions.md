# Copilot Instructions for Local Mind

## Project Overview
Local Mind is an offline-first, cross-platform desktop RAG (Retrieval-Augmented Generation) app for intelligent document analysis. It features advanced citation, highlighting, and privacy—no data leaves the user's machine. The stack includes:
- **Frontend**: React + TypeScript (src/), Shadcn UI, Zustand for state
- **Desktop**: Tauri (Rust, src-tauri/)
- **Backend**: Python FastAPI (backend/), launched as a Tauri sidecar
- **Vector DB**: LanceDB (embedded, file-based)

## Architecture & Data Flow
- **Frontend** (src/): React app communicates with the backend via HTTP (localhost, OpenAI-compatible endpoints). State is managed with Zustand. UI uses split panes and custom overlays for document highlights.
- **Backend** (backend/): FastAPI exposes endpoints for chat, document management, and search. Business logic is in `services/`. Document chunking preserves position metadata for precise citation/highlighting.
- **Tauri** (src-tauri/): Orchestrates the desktop app, launches the Python backend as a sidecar, and manages system integration.
- **Data**: Documents and LanceDB files are stored in `backend/data/`. User config is platform-specific (see backend/README.md).

## Developer Workflows
- **Frontend**: Use Bun (preferred) or npm. Run `bun install` then `bun run dev` (see README.md).
- **Backend**: Setup Python venv, install requirements, run with `./run_dev.sh` or `python main.py`.
- **Tauri**: Build/run desktop app with `bun run tauri dev` (after backend is running).
- **Testing**: No formal test suite yet—manual testing via the UI and API docs (`/docs`).

## Key Conventions & Patterns
- **API**: All backend endpoints are under `/api/v1/`. Chat and document operations use JSON payloads.
- **State**: Use Zustand stores for global state (see `src/stores/`).
- **Component Structure**: UI is modular, with split panes (`ResizablePanelGroup`), chat/message components, and document viewers.
- **Error Handling**: Frontend retries failed chat requests (see `ChatDetails.tsx`). User-friendly error messages are shown for backend/model issues.
- **Document References**: Citations and highlights are passed as structured metadata from backend to frontend, enabling clickable references.
- **Model Integration**: Supports local LLMs via OpenAI-compatible APIs (Ollama, vLLM, llamacpp). Model/server URLs are configurable.

## Integration Points
- **Ollama/vLLM/llamacpp**: For local LLM inference, ensure the model server is running and accessible.
- **LanceDB**: Used for vector search; all document chunking includes position metadata for highlighting.
- **Tauri Sidecar**: Python backend is started/stopped by Tauri; do not run it separately in production builds.

## Examples
- See `src/pages/ChatDetails.tsx` for chat flow, error handling, and citation UI.
- See `backend/services/` for RAG pipeline and document processing logic.
- See `backend/README.md` for backend setup and architecture diagram.

---

**When in doubt, prefer Bun for JS workflows, keep all data local, and preserve document position metadata for citations/highlighting.**
