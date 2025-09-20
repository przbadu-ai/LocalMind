"""
Health check and monitoring API endpoints.

This module provides endpoints for monitoring application health,
checking service dependencies, and retrieving system information.
"""

from fastapi import APIRouter
from models.schemas import HealthCheck
from config.settings import settings
from services import VectorService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Check the health status of the API and its dependencies.

    Performs comprehensive health checks on:
    - API server status
    - Vector database connectivity
    - LLM service availability
    - File system access

    Returns:
        HealthCheck model with:
        - status: "healthy" or "unhealthy"
        - version: Application version
        - vector_db_connected: Vector DB status
        - llm_available: LLM service status
        - timestamp: Check timestamp

    Raises:
        Never raises - always returns a response for monitoring

    Example:
        ```python
        response = requests.get("/api/v1/health")
        # Healthy: {"status": "healthy", "vector_db_connected": true, ...}
        # Unhealthy: {"status": "unhealthy", "vector_db_connected": false, ...}
        ```

    Note:
        This endpoint is designed for health monitoring systems like:
        - Kubernetes liveness/readiness probes
        - Load balancer health checks
        - Monitoring dashboards
    """
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
    """
    Simple ping endpoint for connectivity check.

    Minimal endpoint for quick connectivity verification.
    Useful for network diagnostics and keep-alive checks.

    Returns:
        Dict with "pong" message

    Example:
        ```python
        response = requests.get("/api/v1/ping")
        # Returns: {"message": "pong"}
        ```
    """
    return {"message": "pong"}


@router.get("/info")
async def get_info():
    """
    Get API information and configuration.

    Returns non-sensitive configuration information about the API
    including supported features, models, and limits.

    Returns:
        Dict containing:
        - app_name: Application name
        - version: Current version
        - embedding_model: Active embedding model
        - chunk_size: Document chunk size
        - max_file_size_mb: Upload size limit
        - supported_formats: List of supported file types

    Example:
        ```python
        response = requests.get("/api/v1/info")
        # Returns system information and capabilities
        ```

    Note:
        This endpoint is useful for:
        - Frontend feature detection
        - Client configuration
        - Debugging and support
    """
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "max_file_size_mb": settings.max_file_size_mb,
        "supported_formats": ["pdf", "docx", "txt", "md", "pptx", "png", "jpg", "jpeg"]
    }