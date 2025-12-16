# LocalMind Development Guide

This guide covers setting up your development environment, running the application, and contributing to the project.

## Prerequisites

### Required Tools

1. **Bun** (recommended) or Node.js 18+
   ```bash
   # Install Bun
   curl -fsSL https://bun.sh/install | sh
   ```

2. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

3. **uv** (Python package manager)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. **Rust** (for Tauri)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

5. **Ollama** (or other LLM server)
   ```bash
   # Install from https://ollama.ai/
   ollama pull llama3:instruct
   ```

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/LocalMind.git
cd LocalMind
```

### 2. Install Frontend Dependencies

```bash
bun install
```

### 3. Setup Python Backend

```bash
cd backend

# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -r requirements.txt

cd ..
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or your preferred editor
```

Key settings to configure:

```env
# LLM Configuration
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3:instruct

# Backend Server
BACKEND_HOST=127.0.0.1
BACKEND_PORT=52817

# Database
DATABASE_PATH=./data/local_mind.db
```

## Running the Application

### Development Mode

**Terminal 1 - Backend:**

```bash
cd backend
source .venv/bin/activate
uv run uvicorn main:app --host 127.0.0.1 --port 52817 --reload
```

**Terminal 2 - Frontend:**

```bash
bun dev
```

Access the app at http://localhost:1420

### Tauri Desktop Mode

```bash
bun tauri dev
```

This starts both frontend and Tauri, but you still need to run the backend separately.

### API Documentation

With the backend running, access:
- Swagger UI: http://127.0.0.1:52817/docs
- ReDoc: http://127.0.0.1:52817/redoc

## Project Structure

```
LocalMind/
├── src/                    # React frontend
├── src-tauri/              # Tauri (Rust) app
├── backend/                # Python FastAPI backend
├── docs/                   # Documentation
├── data/                   # SQLite database (auto-created)
├── app.config.json         # App configuration
├── .env                    # Environment variables
└── .env.example            # Environment template
```

## Backend Development

### Adding a New Endpoint

1. Create route file in `backend/api/`:

```python
# backend/api/example.py
from fastapi import APIRouter

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/")
async def get_examples():
    return {"examples": []}

@router.post("/")
async def create_example(data: dict):
    return {"id": "example_123", **data}
```

2. Register router in `backend/main.py`:

```python
from backend.api import example

app.include_router(example.router, prefix="/api/v1")
```

### Adding a New Repository

1. Create repository in `backend/database/repositories/`:

```python
# backend/database/repositories/example_repository.py
from backend.database.connection import get_db

class ExampleRepository:
    def __init__(self):
        self.db = get_db()

    def get_all(self) -> list:
        cursor = self.db.execute("SELECT * FROM examples")
        return cursor.fetchall()

    def create(self, data: dict) -> str:
        # Implementation
        pass

example_repository = ExampleRepository()
```

2. Add table schema in `backend/database/connection.py`:

```python
def init_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS examples (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
```

### Adding a New Pydantic AI Agent

1. Create agent in `backend/agents/`:

```python
# backend/agents/example_agent.py
from dataclasses import dataclass
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

@dataclass
class ExampleDeps:
    context: str

class ExampleResult(BaseModel):
    summary: str
    confidence: float

def create_example_agent() -> Agent[ExampleDeps, ExampleResult]:
    model = OpenAIModel(...)

    agent = Agent(
        model=model,
        deps_type=ExampleDeps,
        result_type=ExampleResult,
        system_prompt="You are an expert at...",
    )

    @agent.tool
    def analyze_context(ctx: RunContext[ExampleDeps]) -> str:
        return ctx.deps.context

    return agent
```

### Running Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

## Frontend Development

### Adding a New Page

1. Create page component in `src/pages/`:

```tsx
// src/pages/Example.tsx
import { useEffect, useState } from "react"
import { useHeaderStore } from "@/stores"

export default function Example() {
  const setTitle = useHeaderStore((s) => s.setTitle)

  useEffect(() => {
    setTitle("Example Page")
    return () => setTitle("")
  }, [setTitle])

  return (
    <div className="p-4">
      <h1>Example Page</h1>
    </div>
  )
}
```

2. Add route in `src/AppRoutes.tsx`:

```tsx
import Example from "./pages/Example"

export default function AppRoutes() {
  return (
    <Routes>
      {/* ... existing routes ... */}
      <Route path="/example" element={<Example />} />
    </Routes>
  )
}
```

3. Add navigation link in `src/components/app-sidebar.tsx`:

```tsx
const navigationItems = [
  { title: "Chats", url: "/chats", icon: MessageSquare },
  { title: "Example", url: "/example", icon: ExampleIcon },
  { title: "Settings", url: "/settings", icon: Settings },
]
```

### Adding a New Service

```typescript
// src/services/example-service.ts
import { API_BASE_URL } from "@/config/app-config"

export interface Example {
  id: string
  name: string
}

class ExampleService {
  private baseUrl = `${API_BASE_URL}/api/v1/example`

  async getAll(): Promise<Example[]> {
    const response = await fetch(this.baseUrl)
    if (!response.ok) throw new Error("Failed to fetch examples")
    return response.json()
  }

  async create(data: Partial<Example>): Promise<Example> {
    const response = await fetch(this.baseUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error("Failed to create example")
    return response.json()
  }
}

export const exampleService = new ExampleService()
```

### Adding a New Zustand Store

```typescript
// src/stores/useExampleStore.ts
import { create } from "zustand"
import { persist } from "zustand/middleware"

interface ExampleState {
  items: string[]
  addItem: (item: string) => void
  removeItem: (item: string) => void
  reset: () => void
}

export const useExampleStore = create<ExampleState>()(
  persist(
    (set) => ({
      items: [],
      addItem: (item) => set((s) => ({ items: [...s.items, item] })),
      removeItem: (item) => set((s) => ({
        items: s.items.filter((i) => i !== item)
      })),
      reset: () => set({ items: [] }),
    }),
    { name: "example-store" }
  )
)
```

### Adding UI Components with Shadcn

```bash
# Add a new Shadcn component
bunx shadcn@latest add button
bunx shadcn@latest add dialog
bunx shadcn@latest add form
```

## Database Migrations

Currently, schema changes require manual migration. For a new table:

1. Update `backend/database/connection.py`:

```python
def init_schema(conn):
    # ... existing tables ...

    conn.execute("""
        CREATE TABLE IF NOT EXISTS new_table (
            id TEXT PRIMARY KEY,
            ...
        )
    """)
```

2. For existing databases, create a migration script:

```python
# scripts/migrate_001.py
import sqlite3

def migrate(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        ALTER TABLE existing_table ADD COLUMN new_column TEXT
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate("./data/local_mind.db")
```

## Code Style

### Python

- Use type hints
- Follow PEP 8
- Use async/await for I/O operations
- Document public functions with docstrings

```python
async def fetch_transcript(video_id: str) -> Transcript:
    """
    Fetch a YouTube video transcript.

    Args:
        video_id: YouTube video ID (11 characters)

    Returns:
        Transcript object with segments

    Raises:
        TranscriptNotFoundError: If transcript unavailable
    """
    ...
```

### TypeScript

- Use TypeScript strict mode
- Prefer functional components with hooks
- Use named exports
- Document complex functions with JSDoc

```typescript
/**
 * Extracts video ID from a YouTube URL.
 * @param url - YouTube URL or video ID
 * @returns Video ID or null if invalid
 */
export function extractVideoId(url: string): string | null {
  // ...
}
```

## Building for Production

### Build Desktop App

```bash
bun tauri build
```

Output will be in `src-tauri/target/release/`.

### Build Frontend Only

```bash
bun build
```

Output will be in `dist/`.

## Troubleshooting

### Backend Won't Start

1. Check Python version:
   ```bash
   python --version  # Needs 3.11+
   ```

2. Reinstall dependencies:
   ```bash
   cd backend
   uv pip install -r requirements.txt --force-reinstall
   ```

3. Check port availability:
   ```bash
   lsof -i :52817
   ```

### LLM Connection Issues

1. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Check .env settings match your LLM server

3. Test the endpoint:
   ```bash
   curl http://localhost:11434/v1/models
   ```

### Frontend Build Errors

1. Clear cache and reinstall:
   ```bash
   rm -rf node_modules bun.lockb
   bun install
   ```

2. Check for TypeScript errors:
   ```bash
   bun tsc --noEmit
   ```

### Database Issues

1. Reset database:
   ```bash
   rm -f data/local_mind.db
   # Restart backend to recreate
   ```

2. Check database schema:
   ```bash
   sqlite3 data/local_mind.db ".schema"
   ```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes following code style guidelines
4. Test your changes
5. Commit with descriptive messages
6. Push and create a Pull Request

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(youtube): add transcript search functionality`
- `fix(chat): resolve streaming connection timeout`
- `docs(readme): update installation instructions`
