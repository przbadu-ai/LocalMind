"""
Chat service for RAG-based conversation management.

This module implements the core RAG (Retrieval-Augmented Generation) pipeline,
managing conversations, context retrieval, and response generation.
"""

import uuid
import time
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime, timezone
from openai import AsyncOpenAI
from models.schemas import ChatRequest, ChatResponse, Citation, SearchQuery
from services.vector_service import VectorService
from services.database_service import database_service
from models.database import get_db
from config.app_settings import config as app_config, OLLAMA_BASE_URL, LLM_MODEL
from core.exceptions import LLMConnectionError
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for handling chat interactions and RAG pipeline.

    This service orchestrates the complete RAG workflow:
    1. Context retrieval from vector store
    2. Citation building from matched documents
    3. LLM response generation with context
    4. Conversation history management

    Attributes:
        vector_service: Service for vector store operations
        conversations: In-memory storage for conversation histories
    """

    def __init__(self, vector_service: VectorService):
        """
        Initialize the chat service.

        Args:
            vector_service: Vector store service instance
        """
        self.vector_service = vector_service
        self.conversations = {}  # TODO: Replace with persistent storage

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat request through the RAG pipeline.

        This method:
        1. Retrieves relevant context based on the query
        2. Builds citations from matched documents
        3. Generates a response using the LLM with context
        4. Stores the conversation for continuity

        Args:
            request: ChatRequest with message and parameters

        Returns:
            ChatResponse with generated text, citations, and metadata

        Raises:
            LLMConnectionError: If LLM service is unavailable
        """
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

            # Generate response
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
                "timestamp": datetime.now(timezone.utc)
            })
            self.conversations[conversation_id].append({
                "role": "assistant",
                "content": response_text,
                "citations": [c.model_dump() for c in citations],
                "timestamp": datetime.now(timezone.utc)
            })

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            return ChatResponse(
                response=response_text,
                conversation_id=conversation_id,
                citations=citations,
                tokens_used=None,  # Will be populated when token counting is added
                response_time_ms=response_time_ms
            )

        except Exception as e:
            logger.error(f"Chat processing failed: {str(e)}")
            raise LLMConnectionError(f"Failed to process chat: {str(e)}")

    async def _generate_response(self, query: str, context: str, temperature: float) -> str:
        """
        Generate response using OpenAI-compatible API (Ollama/LlamaCpp).

        Args:
            query: User's query
            context: Retrieved context from documents
            temperature: LLM temperature for response variability

        Returns:
            Generated response text
        """
        try:
            # Get LLM configuration from centralized config
            llm_config = app_config.get_llm_config()

            # Build messages for chat completion
            messages = []

            if context:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided context. Use the context to provide accurate and relevant information."
                })
                messages.append({
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}\n\nPlease answer the question based on the context provided above."
                })
            else:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful assistant."
                })
                messages.append({
                    "role": "user",
                    "content": query
                })

            # Initialize OpenAI client with the correct endpoint
            base_url = app_config.get_openai_base_url()
            api_key = llm_config.get('api_key') or "sk-no-key-needed"

            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )

            # Generate response
            response = await client.chat.completions.create(
                model=llm_config["model"],
                messages=messages,
                temperature=temperature,
                max_tokens=1024,
                stream=False
            )

            return response.choices[0].message.content or "I couldn't generate a response."

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            error_msg = str(e).lower()
            if "connection" in error_msg or "connect" in error_msg or "refused" in error_msg:
                raise LLMConnectionError(
                    "Cannot connect to LLM service. Please ensure:\n"
                    "• Ollama is running (ollama serve)\n"
                    "• Or LlamaCpp server is running\n"
                    f"• Service is accessible at {llm_config['base_url']}"
                )
            raise LLMConnectionError(f"Failed to generate response: {str(e)}")

    def _build_context(self, search_results: List[Any]) -> str:
        """
        Build formatted context string from search results.

        Combines multiple search results into a structured context
        that can be passed to the LLM for response generation.

        Args:
            search_results: List of search results from vector store

        Returns:
            Formatted context string with source attribution
        """
        if not search_results:
            return ""

        context_parts = []
        for i, result in enumerate(search_results[:5], 1):  # Limit to top 5 results
            context_parts.append(
                f"[Source {i} - {result.document_name}]: {result.text}"
            )

        return "\n\n".join(context_parts)

    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve complete conversation history.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            List of messages with roles, content, and timestamps
        """
        return self.conversations.get(conversation_id, [])

    async def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear/delete a conversation from memory.

        Args:
            conversation_id: Conversation to clear

        Returns:
            True if conversation was cleared, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat responses using OpenAI-compatible streaming API.

        This method yields response chunks as they're generated,
        providing real-time feedback to the user.

        Args:
            request: ChatRequest with message and parameters

        Yields:
            Dict containing response chunks and metadata

        Raises:
            LLMConnectionError: If LLM service is not available
        """
        try:
            # Get database session
            db = next(get_db())
            start_time = time.time()

            # Get or create chat
            conversation_id = request.conversation_id
            chat = database_service.get_or_create_chat(db, conversation_id)
            conversation_id = chat.id

            # Save user message to database
            user_message = database_service.add_message(
                db,
                chat_id=conversation_id,
                role="user",
                content=request.message
            )

            # Retrieve context if needed
            context = ""
            citations = []

            if request.include_citations:
                search_query = SearchQuery(
                    query=request.message,
                    limit=request.max_results
                )
                context_results = await self.vector_service.search(search_query)

                # Build citations
                for result in context_results:
                    citations.append({
                        "text": result.text[:200],
                        "document_id": result.document_id,
                        "document_name": result.document_name,
                        "page": result.metadata.page if result.metadata else None,
                        "confidence": result.score
                    })

                context = self._build_context(context_results)

            # Get LLM configuration from centralized config
            llm_config = app_config.get_llm_config()

            # Build messages for chat completion
            messages = []

            if context:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided context."
                })
                messages.append({
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {request.message}\n\nPlease answer the question based on the context provided above."
                })
            else:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful assistant."
                })
                messages.append({
                    "role": "user",
                    "content": request.message
                })

            # Initialize OpenAI client with Ollama/LlamaCpp endpoint
            base_url = llm_config['base_url']
            if not base_url.endswith('/v1'):
                base_url = f"{base_url}/v1"

            client = AsyncOpenAI(
                api_key="sk-no-key-needed",  # Ollama/LlamaCpp don't need real keys
                base_url=base_url
            )

            # First, send metadata
            yield {
                "type": "metadata",
                "conversation_id": conversation_id,
                "citations": citations
            }

            # Stream the response
            full_response = ""
            stream = await client.chat.completions.create(
                model=llm_config["model"],
                messages=messages,
                temperature=request.temperature,
                max_tokens=1024,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    full_response += chunk_text

                    yield {
                        "type": "content",
                        "content": chunk_text,
                        "done": False
                    }

            # Save assistant message to database
            processing_time_ms = int((time.time() - start_time) * 1000)

            assistant_message = database_service.add_message(
                db,
                chat_id=conversation_id,
                role="assistant",
                content=full_response,
                metadata={
                    "citations": citations,
                    "processing_time_ms": processing_time_ms,
                    "context": context if context else None
                }
            )

            # Close database session
            db.close()

            yield {
                "type": "done",
                "total_response": full_response,
                "message_id": assistant_message.id if assistant_message else None
            }

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            # Try to close database session if it exists
            try:
                if 'db' in locals():
                    db.close()
            except:
                pass

            error_msg = str(e).lower()
            if "connection" in error_msg or "connect" in error_msg or "refused" in error_msg:
                yield {
                    "type": "error",
                    "error": "Cannot connect to LLM service. Please ensure Ollama or LlamaCpp is running."
                }
            else:
                yield {
                    "type": "error",
                    "error": str(e)
                }