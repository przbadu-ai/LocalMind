from fastapi import APIRouter, Depends
from models.schemas import HealthCheck
from config import settings
from services import VectorService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Check the health status of the API and its dependencies."""
    try:
        # Check vector DB connection
        vector_service = VectorService()
        stats = await vector_service.get_stats()
        vector_db_connected = "error" not in stats

        # Check LLM availability (will be implemented)
        llm_available = False  # Will be updated when LLM is integrated

        return HealthCheck(
            status="healthy",
            version=settings.app_version,
            vector_db_connected=vector_db_connected,
            llm_available=llm_available
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            version=settings.app_version,
            vector_db_connected=False,
            llm_available=False
        )


@router.get("/ping")
async def ping():
    """Simple ping endpoint for connectivity check."""
    return {"message": "pong"}


@router.get("/info")
async def get_info():
    """Get API information and configuration."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "max_file_size_mb": settings.max_file_size_mb,
        "supported_formats": ["pdf", "docx", "txt", "md", "pptx", "png", "jpg", "jpeg"]
    }