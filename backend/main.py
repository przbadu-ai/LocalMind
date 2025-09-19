"""
Local Mind Backend API Server

This is the main entry point for the FastAPI backend server that powers
the Local Mind desktop application. It provides REST APIs for:
- Document management and processing
- Vector-based semantic search
- RAG-powered chat interactions
- Configuration management

The server can be run as a Tauri sidecar process or standalone for development.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import settings
from core import setup_middlewares, setup_exception_handlers
from api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.

    Handles startup and shutdown operations:
    - Startup: Initialize services, create directories, load models
    - Shutdown: Clean up resources, save state

    Args:
        app: FastAPI application instance

    Yields:
        Control back to FastAPI during application runtime
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Debug mode: {settings.debug}")

    # TODO: Add startup tasks like:
    # - Pre-load embedding model
    # - Verify LLM connectivity
    # - Initialize database connections

    yield

    # Shutdown
    logger.info("Shutting down application")
    # TODO: Add cleanup tasks


# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Open-source, offline-first desktop RAG application.

    Features:
    - 🔒 Fully offline document processing
    - 🔍 Semantic search with vector embeddings
    - 💬 RAG-powered chat with citations
    - 📄 Support for PDF, DOCX, TXT, MD, PPTX
    - 🎯 Precise document highlighting
    - ⚙️ Configurable LLM providers
    """,
    lifespan=lifespan,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware
setup_middlewares(app)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint - redirects to API documentation.

    Returns:
        RedirectResponse to /docs
    """
    return RedirectResponse(url="/docs")


@app.get("/api", include_in_schema=False)
async def api_root():
    """
    API root information endpoint.

    Provides basic information about the API including version,
    documentation links, and health check endpoint.

    Returns:
        Dict with API metadata
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",
        "documentation": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.api_prefix}/health",
        "description": "Local Mind Backend API"
    }


if __name__ == "__main__":
    """
    Run the application directly for development.

    In production, this will be run as a Tauri sidecar process.
    For development, you can run: DEBUG=true python main.py
    """
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )