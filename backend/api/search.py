from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from models.schemas import SearchQuery, SearchResult
from services import VectorService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
vector_service = VectorService()


@router.post("/", response_model=List[SearchResult])
async def search_documents(search_query: SearchQuery):
    """Perform semantic search across documents."""
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
    """Perform semantic search across documents (GET method for easy testing)."""
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
    """Get statistics about the vector store."""
    try:
        stats = await vector_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))