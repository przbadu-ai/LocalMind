"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.connection import init_db

# Initialize database early - before routers are imported
# This ensures tables exist even in reload mode
init_db()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting LocalMind backend...")
    logger.info(f"Database path: {settings.database_full_path}")
    logger.info(f"LLM provider: {settings.llm_provider}")
    logger.info(f"LLM base URL: {settings.llm_base_url}")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down LocalMind backend...")


# Create FastAPI app
app = FastAPI(
    title="LocalMind API",
    description="Backend API for LocalMind - LLM chat with YouTube transcription",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


# Import and include routers
from api import chat, chats, mcp, settings as settings_router, youtube

app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(chats.router, prefix="/api/v1", tags=["Chats"])
app.include_router(youtube.router, prefix="/api/v1", tags=["YouTube"])
app.include_router(mcp.router, prefix="/api/v1", tags=["MCP"])
app.include_router(settings_router.router, prefix="/api/v1", tags=["Settings"])


def main():
    """Run the server."""
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
