from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

# Add backend directory to path
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
    """Manage application lifecycle."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Debug mode: {settings.debug}")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Open-source, offline-first desktop RAG application",
    lifespan=lifespan,
    debug=settings.debug
)

# Setup middleware
setup_middlewares(app)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/api", include_in_schema=False)
async def api_root():
    """API root information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",
        "documentation": "/docs",
        "health": f"{settings.api_prefix}/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )