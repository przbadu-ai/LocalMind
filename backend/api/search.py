"""
Semantic search API endpoints.

This module provides vector-based semantic search capabilities
for finding relevant content across all indexed documents.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from models.schemas import SearchQuery, SearchResult
from services import VectorService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
vector_service = VectorService()


@router.post("/", response_model=List[SearchResult])
async def search_documents(search_query: SearchQuery):
    """
    Perform semantic search across documents.

    Uses vector similarity to find relevant content based on meaning
    rather than exact keyword matches. Returns results ranked by
    semantic similarity.

    Args:
        search_query: SearchQuery with:
        - query: Search text
        - limit: Max results (1-100)
        - document_ids: Optional document filter
        - min_score: Minimum similarity threshold (0.0-1.0)

    Returns:
        List of SearchResult objects sorted by relevance

    Raises:
        HTTPException: 500 if search fails

    Example:
        ```python
        response = requests.post("/api/v1/search/", json={
            "query": "machine learning algorithms",
            "limit": 10,
            "min_score": 0.7
        })
        # Returns relevant chunks with similarity scores
        ```

    Note:
        Semantic search finds conceptually similar content even when
        exact words don't match. For example, searching for "car"
        might also find content about "automobile" or "vehicle".
    """
    try:
        results = await vector_service.search(search_query)
        return results
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[SearchResult])
async def search_documents_get(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    min_score: float = Query(0.7, ge=0, le=1, description="Minimum similarity score")
):
    """
    Perform semantic search (GET method for easy testing).

    Convenience endpoint for testing search functionality via browser
    or simple HTTP GET requests. Functionally identical to POST version.

    Args:
        q: Search query text
        limit: Maximum results to return (1-100, default: 10)
        min_score: Minimum similarity score (0.0-1.0, default: 0.7)

    Returns:
        List of SearchResult objects sorted by relevance

    Raises:
        HTTPException: 500 if search fails

    Example:
        ```
        GET /api/v1/search/?q=machine+learning&limit=5&min_score=0.8
        ```

    Note:
        This GET endpoint is useful for:
        - Quick testing in browser
        - Simple integrations
        - Debugging search queries
    """
    try:
        search_query = SearchQuery(
            query=q,
            limit=limit,
            min_score=min_score
        )
        results = await vector_service.search(search_query)
        return results
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_vector_stats():
    """
    Get statistics about the vector store.

    Provides insights into the vector database including document
    counts, chunk statistics, and storage information.

    Returns:
        Dict containing:
        - total_documents: Number of unique documents
        - total_chunks: Total text chunks indexed
        - embedding_model: Model used for embeddings
        - database_path: Vector DB storage location

    Raises:
        HTTPException: 500 if stats retrieval fails

    Example:
        ```python
        response = requests.get("/api/v1/search/stats")
        # Returns:
        # {
        #   "total_documents": 42,
        #   "total_chunks": 1337,
        #   "embedding_model": "all-MiniLM-L6-v2",
        #   "database_path": "/path/to/lancedb"
        # }
        ```

    Note:
        Useful for:
        - Monitoring database growth
        - Debugging search issues
        - Capacity planning
        - Admin dashboards
    """
    try:
        stats = await vector_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))