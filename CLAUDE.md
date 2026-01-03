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

## Deployment Strategy

### Dual Deployment Architecture
LocalMind supports **two deployment modes** for different use cases:

#### 1. Desktop Application (Primary/End-User)
**Purpose**: Offline-first, privacy-focused native desktop application

**Distribution**:
- Multi-platform Tauri bundles (Windows `.msi`, Linux `.deb`/`.AppImage`, macOS `.dmg`)
- GitHub Releases for public distribution
- Open source under Apache 2.0 License

**Build Configuration**:
- File: `src-tauri/tauri.conf.json`
- Product name: `local-mind`
- Identifier: `com.przbadu.local-mind`
- Version: `0.1.0`

**Build Commands**:
```bash
# Development
bun run tauri dev

# Production build
bun run tauri build
```

**Planned CI/CD**: GitHub Actions for automated multi-platform builds

#### 2. Web Application (Server/Development)
**Purpose**: Dockerized web deployment for server hosting or team access

**Deployment Methods**:

##### Kamal Deployment (Production)
- **File**: `config/deploy.yml`
- **Registry**: GitHub Container Registry (`ghcr.io/przbadu/localmind`)
- **Target Server**: `192.168.1.173` (LAN deployment)
- **Services**:
  - Frontend: nginx serving React app (port 80)
  - Backend: Python FastAPI (port 8001)
- **Volumes**: `/var/data/localmind` for persistent storage

**Deployment - Just one command:**
```bash
kamal deploy    # Deploys BOTH frontend and backend
```

The pre-deploy hook (`.kamal/hooks/pre-deploy`) automatically:
1. Builds the backend Docker image
2. Pushes it to the registry
3. Deploys and restarts the backend container
4. Waits for health check
5. Then Kamal deploys the frontend

**Base Image (for fast builds):**
The backend uses a pre-built base image (`ghcr.io/przbadu/localmind-base:latest`) with heavy dependencies (docling, PyTorch) pre-installed. This reduces build times from ~40 minutes to ~30 seconds.

```bash
# Rebuild base image (only when docling/Python version changes):
./scripts/build-base-image.sh
```

**Other Kamal commands:**
```bash
kamal setup      # Initial deployment (first time only)
kamal app logs   # View frontend logs
kamal rollback   # Rollback frontend to previous version
```

**View backend logs:**
```bash
ssh root@192.168.1.173 "docker logs localmind-backend --tail 100"
```

##### Docker Compose (Local Development)
- **File**: `docker-compose.yml`
- **Services**:
  - Frontend: `http://localhost:3000`
  - Backend: `http://localhost:52817`
- **Features**: Health checks, auto-restart, persistent volumes
- **Commands**:
  ```bash
  docker-compose up -d      # Start services
  docker-compose down       # Stop services
  docker-compose logs -f    # View logs
  ```

##### Docker Configuration Details
- **Frontend Dockerfile**: Multi-stage build with nginx
  - Build command: `bun run build:frontend` (excludes Tauri)
  - Uses `docker/nginx.conf.template` for dynamic backend routing
  - Environment vars: `BACKEND_HOST`, `BACKEND_PORT`
- **Backend Dockerfile**: Python FastAPI with uvicorn
  - Mounts `app.config.json` for configuration
  - Accesses host Ollama via `host.docker.internal:11434`
  - Database persists at `/app/data/local_mind.db`

### Key Architectural Differences

| Aspect | Desktop (Tauri) | Web (Docker) |
|--------|----------------|--------------|
| **Offline** | Fully offline | Requires network for LLM |
| **Database** | Local SQLite | Shared/persistent volume |
| **Distribution** | Download & install | Access via browser |
| **Updates** | Manual/auto-update | Deploy via Kamal/compose |
| **Privacy** | 100% local | Server-hosted |
| **Target Users** | Privacy-focused individuals | Teams/multi-user access |

### Deployment Environment
- **LLM Server**: Ollama at `192.168.1.173:11434`
- **Backend Port**: `52817` (development), `8001` (Kamal production)
- **Frontend Port**: `1420` (dev), `3000` (Docker Compose), `80` (Kamal)
- **Data Persistence**: `/var/data/localmind` (production server)

## Configuration Management

### Centralized Configuration System
The application uses a single `app.config.json` file at the project root as the source of truth for all configuration. This eliminates duplication and ensures consistency across frontend and backend.

**Configuration Files:**
- `app.config.json` - Main configuration file (single source of truth)
- `backend/config/app_settings.py` - Python configuration loader (reads from app.config.json)
- `backend/config/settings.py` - Backward compatibility wrapper
- `backend/config/config_manager.py` - User-specific runtime overrides
- `src/config/app-config.ts` - TypeScript configuration loader

**Import Patterns:**
```python
# Backend - ALWAYS use this pattern:
from config.settings import settings  # For backward compatibility
from config.app_settings import APP_NAME, BACKEND_PORT  # For direct imports

# NOT this (imports module, not instance):
from config import settings  # WRONG - this imports the module
```

```typescript
// Frontend
import { API_BASE_URL, DEFAULT_LLM_MODEL } from "@/config/app-config"
```

### Configuration Migration Guidelines
When updating configuration:
1. Modify values only in `app.config.json`
2. Never hardcode URLs, ports, or model names
3. Always check import paths are correct (module.instance pattern)
4. Test backend startup after configuration changes

### Common Configuration Pitfalls to Avoid
1. **Import Error**: Using `from config import settings` instead of `from config.settings import settings`
2. **Missing Properties**: Not exposing required properties in compatibility wrappers
3. **Hardcoded Values**: Duplicating configuration values instead of referencing app.config.json
4. **Path Issues**: Not handling relative vs absolute paths correctly in configuration

### LLM Configuration
- Default model: `llama3:instruct`
- Ollama host: `192.168.1.173:11434`
- Backend port: `52817`
- All LLM settings centralized in app.config.json

## Database Migration System

### IMPORTANT: Always Use Migrations for Database Changes
**NEVER modify the database schema directly.** All database changes MUST go through the migration system.

### Migration System Overview
- Location: `backend/database/migrations/`
- Runner: `backend/database/migrator.py`
- Tracking table: `schema_migrations`
- Migrations run automatically on backend startup via `init_db()`

### Creating a New Migration
1. Create a new file in `backend/database/migrations/` with timestamp prefix:
   ```
   YYYYMMDDHHMMSS_description.py
   ```
   Example: `20241220150000_add_user_preferences.py`

2. Use this template:
   ```python
   """Description of what this migration does."""

   import sqlite3

   VERSION = "20241220150000"
   DESCRIPTION = "Add user preferences table"

   def up(conn: sqlite3.Connection) -> None:
       """Apply the migration."""
       # For new tables:
       conn.execute("""
           CREATE TABLE IF NOT EXISTS user_preferences (
               id TEXT PRIMARY KEY,
               key TEXT UNIQUE NOT NULL,
               value JSON
           )
       """)

       # For adding columns (always check if exists first):
       cursor = conn.execute("PRAGMA table_info(some_table)")
       columns = [row[1] for row in cursor.fetchall()]
       if "new_column" not in columns:
           conn.execute("ALTER TABLE some_table ADD COLUMN new_column TEXT")
   ```

### Migration Best Practices
1. **Always use `IF NOT EXISTS`** for CREATE TABLE statements
2. **Always check column existence** before ALTER TABLE ADD COLUMN
3. **Migrations must be idempotent** - safe to run multiple times
4. **Never modify existing migrations** - create new ones instead
5. **Test migrations locally** before deploying
6. **Include data migrations** when needed (e.g., migrating data between tables)

### Common Migration Patterns

**Adding a new table:**
```python
def up(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS new_table (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
```

**Adding a column:**
```python
def up(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("PRAGMA table_info(existing_table)")
    columns = [row[1] for row in cursor.fetchall()]
    if "new_column" not in columns:
        conn.execute("ALTER TABLE existing_table ADD COLUMN new_column TEXT DEFAULT ''")
```

**Adding an index:**
```python
def up(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE INDEX IF NOT EXISTS idx_table_column ON table_name(column_name)")
```

**Migrating data between tables:**
```python
def up(conn: sqlite3.Connection) -> None:
    # Create new table
    conn.execute("CREATE TABLE IF NOT EXISTS new_table (...)")

    # Migrate data from old location
    cursor = conn.execute("SELECT * FROM old_table WHERE ...")
    for row in cursor.fetchall():
        conn.execute("INSERT INTO new_table (...) VALUES (...)", row)

    # Optionally clean up old data
    conn.execute("DELETE FROM old_table WHERE ...")
```

### Checking Migration Status
```python
from database.migrator import get_migration_status
from database.connection import get_db

with get_db() as conn:
    status = get_migration_status(conn)
    print(f"Applied: {status['applied_versions']}")
    print(f"Pending: {status['pending_versions']}")
```