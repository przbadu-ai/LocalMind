# 📋 Illuminate Development Tasks

## Phase 1: Project Setup & Foundation
### Environment Setup
- [x] Initialize Tauri + React + TypeScript project using `npm create tauri-app`
- [x] Set up Python virtual environment for backend
- [x] Install and configure Shadcn UI components
- [x] Set up Git repository and .gitignore
- [x] Configure ESLint and Prettier for TypeScript
- [x] Set up Python linting (Black, Flake8)

### Core Dependencies Installation
- [x] Install React dependencies (zustand, react-router-dom, allotment, @tanstack/react-query)
- [x] Install Python dependencies (FastAPI, uvicorn, lancedb, sentence-transformers, pymupdf)
- [x] Configure Tailwind CSS with Shadcn UI
- [x] Set up Vite configuration for React
- [x] Configure Tauri allowlist permissions (file system, shell, http)

## Phase 2: Backend Development (Python/FastAPI)
### FastAPI Server Setup
- [x] Create basic FastAPI application structure
- [x] Set up CORS middleware for Tauri frontend
- [x] Implement health check endpoint
- [x] Configure uvicorn server settings
- [x] Create Pydantic models for request/response

### Document Processing Module
- [x] Implement PDF text extraction with PyMuPDF
- [x] **Add position tracking for PDF text (bbox coordinates)**
- [x] Implement TXT file processor
- [x] Implement Markdown file processor
- [x] Create document chunking with overlap
- [x] **Preserve position metadata through chunking**
- [x] Add support for DOCX files
- [x] Add support for PPTX files
- [ ] Implement image text extraction (OCR optional)
- [x] Create unified document processor interface

### Vector Store Implementation (LanceDB)
- [x] Set up LanceDB connection and initialization
- [x] Create document table schema with position fields
- [x] Implement document embedding generation (sentence-transformers)
- [x] Create vector insertion methods
- [x] Implement vector similarity search
- [x] **Add position data retrieval methods**
- [x] Implement document deletion/update
- [x] Add metadata filtering capabilities
- [ ] Create backup/restore functionality

## Phase 2: RAG Pipeline
- [x] Implement query embedding generation
- [x] Create context retrieval from vector store
- [x] Build prompt template with context
- [x] **Add citation tracking in responses**
- [x] Implement streaming response generation
- [ ] Add response caching mechanism
- [ ] Create relevance scoring system
- [ ] Implement hybrid search (vector + keyword)

## Phase 2: Model Integration
- [x] Create Ollama integration client
- [x] Add OpenAI-compatible API support
- [ ] Implement model switching logic
- [ ] Add model health checking
- [ ] Create fallback mechanisms
- [ ] Implement token counting/limiting
- [x] Add support for different embedding models

## Phase 3: Frontend Development (React/TypeScript)
### Project Structure
- [ ] Set up folder structure (components, stores, lib, types)
- [ ] Configure path aliases in TypeScript
- [ ] Create API client with Axios
- [ ] Set up React Query for data fetching
- [ ] Configure Zustand stores

### State Management (Zustand)
- [ ] Create document store (documents, active document, highlights)
- [ ] Create chat store (messages, streaming state)
- [ ] Create model store (available models, active model)
- [ ] Add persistence to stores
- [ ] Implement store DevTools integration

### Layout Components
- [ ] Implement main app layout with Allotment
- [ ] Create resizable panel system
- [ ] Add application header/toolbar
- [ ] Implement navigation with React Router
- [ ] Create settings page layout
- [ ] Add model management page

### Document Management
- [ ] Create document upload component
- [ ] Implement drag-and-drop file upload
- [ ] Build document list sidebar
- [ ] Add document search/filter
- [ ] Create document deletion UI
- [ ] Implement document metadata display
- [ ] Add upload progress indicators

### Document Viewer
- [ ] Integrate PDF.js for PDF rendering
- [ ] **Implement highlight overlay system**
- [ ] **Add click-to-navigate functionality**
- [ ] Create page navigation controls
- [ ] Add zoom controls
- [ ] Implement text selection
- [ ] **Create highlight animation effects**
- [ ] Add support for non-PDF documents
- [ ] Implement document search within viewer

### Chat Interface
- [ ] Create message list component
- [ ] Implement message input with send button
- [ ] Add streaming message support
- [ ] **Create CitationLink component**
- [ ] **Implement citation click handlers**
- [ ] Add message history persistence
- [ ] Create typing indicators
- [ ] Implement message actions (copy, retry)
- [ ] Add markdown rendering for messages

### Model Manager
- [ ] Create model list view
- [ ] Implement model download UI
- [ ] Add download progress tracking
- [ ] Create model deletion interface
- [ ] Add model information display
- [ ] Implement model switching UI
- [ ] Create external server configuration

## Phase 4: Tauri Integration
### Backend Integration
- [ ] Configure Python backend as sidecar process
- [ ] Implement backend startup on app launch
- [ ] Add backend health monitoring
- [ ] Create backend restart mechanism
- [ ] Handle backend shutdown on app close

### Native Features
- [ ] Implement native file picker
- [ ] Add system tray integration
- [ ] Create native notifications
- [ ] Implement keyboard shortcuts
- [ ] Add window state persistence
- [ ] Configure auto-updater

### IPC Communication
- [ ] Create Tauri commands for file operations
- [ ] Implement secure API communication
- [ ] Add error handling for IPC calls
- [ ] Create logging system

## Phase 5: Core Features Integration
### Citation System (Killer Feature)
- [ ] **Implement citation extraction from LLM responses**
- [ ] **Create citation-to-chunk mapping**
- [ ] **Build highlight coordinate calculation**
- [ ] **Implement smooth scroll to highlight**
- [ ] **Add highlight persistence during session**
- [ ] **Create highlight preview on hover**
- [ ] **Add citation numbering system**
- [ ] **Implement multi-document citations**

### Search Functionality
- [ ] Implement full-text search across documents
- [ ] Add search result highlighting
- [ ] Create search history
- [ ] Implement search filters (date, type, etc.)
- [ ] Add semantic search capabilities

## Phase 6: Testing & Optimization
### Testing
- [ ] Write unit tests for document processor
- [ ] Test vector store operations
- [ ] Create integration tests for RAG pipeline
- [ ] Test citation accuracy
- [ ] Implement E2E tests with Playwright
- [ ] Test cross-platform compatibility
- [ ] Add performance benchmarks

### Performance Optimization
- [ ] Implement response caching
- [ ] Add lazy loading for documents
- [ ] Optimize vector search queries
- [ ] Implement batch processing
- [ ] Add request debouncing
- [ ] Optimize bundle size
- [ ] Implement virtual scrolling for large lists

### Error Handling
- [ ] Add comprehensive error boundaries
- [ ] Implement retry mechanisms
- [ ] Create user-friendly error messages
- [ ] Add logging system
- [ ] Implement crash reporting

## Phase 7: Polish & UX
### User Experience
- [ ] Add loading states throughout app
- [ ] Implement smooth transitions
- [ ] Create empty states
- [ ] Add tooltips and help text
- [ ] Implement undo/redo functionality
- [ ] Add keyboard navigation
- [ ] Create onboarding flow

### Accessibility
- [ ] Add ARIA labels
- [ ] Implement keyboard shortcuts
- [ ] Ensure color contrast compliance
- [ ] Add screen reader support
- [ ] Test with accessibility tools

### Theming
- [ ] Implement dark/light mode toggle
- [ ] Create theme persistence
- [ ] Add custom theme options
- [ ] Ensure consistent styling

## Phase 8: Distribution & Deployment
### Build Configuration
- [ ] Configure production builds for all platforms
- [ ] Set up code signing for Windows
- [ ] Set up code signing for macOS
- [ ] Create Linux package configurations
- [ ] Optimize build size

### Documentation
- [ ] Write comprehensive README
- [ ] Create user documentation
- [ ] Write API documentation
- [ ] Create developer guide
- [ ] Add contributing guidelines
- [ ] Create video tutorials

### Release Process
- [ ] Set up GitHub Actions for CI/CD
- [ ] Create automated testing pipeline
- [ ] Configure auto-release workflow
- [ ] Set up version management
- [ ] Create changelog generation

### Distribution
- [ ] Create installer for Windows (.exe)
- [ ] Create installer for macOS (.dmg)
- [ ] Create AppImage for Linux
- [ ] Set up auto-updater
- [ ] Create portable versions
- [ ] Submit to package managers (Homebrew, Chocolatey)

## Phase 9: Community & Open Source
### Open Source Setup
- [ ] Choose and add LICENSE file (Apache 2.0)
- [ ] Create CONTRIBUTING.md
- [ ] Set up issue templates
- [ ] Create pull request template
- [ ] Add code of conduct
- [ ] Set up security policy

### Community Building
- [ ] Create project website/landing page
- [ ] Set up Discord server
- [ ] Create social media accounts
- [ ] Write launch blog post
- [ ] Create demo video/GIF
- [ ] Reach out to potential users/contributors

## Phase 10: Future Enhancements (Post-MVP)
### Advanced Features
- [ ] Plugin system architecture
- [ ] Web page import functionality
- [ ] Cloud sync (optional)
- [ ] Collaborative features
- [ ] Mobile companion app
- [ ] Advanced analytics dashboard
- [ ] Custom model fine-tuning interface
- [ ] Batch document processing

---

## 🎯 Priority Order for MVP

### Week 1-2: Foundation
1. Project setup
2. FastAPI backend structure
3. Basic React frontend
4. Tauri configuration

### Week 3-4: Core Backend
1. PDF processing with positions
2. LanceDB integration
3. Basic RAG pipeline
4. Ollama integration

### Week 5-6: Core Frontend
1. Document upload/list
2. Basic PDF viewer
3. Chat interface
4. State management

### Week 7-8: Killer Features
1. **Citation system implementation**
2. **Click-to-highlight functionality**
3. **Position tracking throughout pipeline**
4. Search functionality

### Week 9-10: Polish & Release
1. Testing
2. Documentation
3. Build configuration
4. Initial release

## 📊 Success Metrics

- [ ] Can upload and process PDF documents
- [ ] Can chat with documents and get responses
- [ ] **Citations in responses are clickable**
- [ ] **Clicking citation highlights exact source text**
- [ ] Works completely offline
- [ ] Builds for Windows, Linux, macOS
- [ ] Bundle size under 20MB
- [ ] Query response under 1 second

---

Start with Phase 1 and work through systematically. The **bold** items are the killer features that differentiate Illuminate from other RAG applications. Focus on getting a working MVP with basic features first, then add the citation/highlighting system, then polish.