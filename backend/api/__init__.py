from fastapi import APIRouter
from .health import router as health_router
from .documents import router as documents_router
from .chat import router as chat_router
from .search import router as search_router
from .config import router as config_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(config_router, prefix="/config", tags=["Configuration"])

__all__ = ["api_router"]