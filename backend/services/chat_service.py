import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from models.schemas import ChatRequest, ChatResponse, Citation, SearchQuery
from services.vector_service import VectorService
from config import settings
from core.exceptions import LLMConnectionError
import logging
import json

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat interactions and RAG pipeline."""

    def __init__(self, vector_service: VectorService):
        self.vector_service = vector_service
        self.conversations = {}  # In-memory storage for now

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request with RAG pipeline."""
        start_time = time.time()

        try:
            # Generate or retrieve conversation ID
            conversation_id = request.conversation_id or str(uuid.uuid4())

            # Retrieve relevant context from vector store
            context_results = []
            citations = []

            if request.include_citations:
                search_query = SearchQuery(
                    query=request.message,
                    limit=request.max_results
                )
                context_results = await self.vector_service.search(search_query)

                # Build citations
                for result in context_results:
                    citations.append(Citation(
                        text=result.text[:200],  # Truncate for display
                        document_id=result.document_id,
                        document_name=result.document_name,
                        page=result.metadata.page,
                        bbox=result.metadata.bbox,
                        confidence=result.score
                    ))

            # Build context for LLM
            context = self._build_context(context_results)

            # Generate response (mock for now - will integrate with actual LLM)
            response_text = await self._generate_response(
                request.message,
                context,
                request.temperature
            )

            # Store conversation history
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []

            self.conversations[conversation_id].append({
                "role": "user",
                "content": request.message,
                "timestamp": datetime.utcnow()
            })
            self.conversations[conversation_id].append({
                "role": "assistant",
                "content": response_text,
                "citations": [c.dict() for c in citations],
                "timestamp": datetime.utcnow()
            })

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            return ChatResponse(
                response=response_text,
                conversation_id=conversation_id,
                citations=citations,
                tokens_used=None,  # Will be populated when LLM is integrated
                response_time_ms=response_time_ms
            )

        except Exception as e:
            logger.error(f"Chat processing failed: {str(e)}")
            raise LLMConnectionError(f"Failed to process chat: {str(e)}")

    async def _generate_response(self, query: str, context: str, temperature: float) -> str:
        """Generate response using LLM (mock implementation)."""
        # This will be replaced with actual LLM integration
        # For now, return a mock response
        if context:
            return f"Based on the provided documents, here's what I found regarding '{query}': {context[:500]}..."
        else:
            return f"I'll help you with '{query}'. However, I don't have any specific documents to reference for this query."

    def _build_context(self, search_results: List[Any]) -> str:
        """Build context string from search results."""
        if not search_results:
            return ""

        context_parts = []
        for i, result in enumerate(search_results[:5], 1):  # Limit to top 5 results
            context_parts.append(
                f"[Source {i} - {result.document_name}]: {result.text}"
            )

        return "\n\n".join(context_parts)

    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Retrieve conversation history."""
        return self.conversations.get(conversation_id, [])

    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a specific conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False