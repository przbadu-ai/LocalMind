"""
Vector store service for document embeddings and similarity search.

This module manages the vector database operations using LanceDB,
including embedding generation, storage, and semantic search.
"""

import lancedb
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from config.settings import settings
from core.exceptions import VectorStoreError
from models.schemas import SearchQuery, SearchResult, DocumentMetadata
import logging

logger = logging.getLogger(__name__)


class VectorService:
    """
    Service for managing vector embeddings and similarity search.

    This service provides:
    1. Document embedding generation using sentence transformers
    2. Vector storage in LanceDB (embedded, file-based)
    3. Semantic similarity search with metadata filtering
    4. Document management in the vector store

    Attributes:
        db_path: Path to LanceDB database directory
        embedding_model: SentenceTransformer model for embeddings
        db: LanceDB connection instance
        table: LanceDB table for document vectors
    """

    def __init__(self):
        """
        Initialize the vector service with database and embedding model.

        Creates database connection and loads the embedding model.
        Automatically creates the database table if it doesn't exist.
        """
        self.db_path = str(settings.lancedb_dir)
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.db = None
        self.table = None
        self._initialize_db()

    def _initialize_db(self):
        """
        Initialize LanceDB connection and create table if needed.

        Creates a 'documents' table with the following schema:
        - vector: Embedding vector
        - text: Original text chunk
        - document_id: Parent document identifier
        - document_name: Human-readable document name
        - chunk_id: Unique chunk identifier
        - page: Page number (for PDFs)
        - bbox: Bounding box coordinates

        Raises:
            VectorStoreError: If database initialization fails
        """
        try:
            self.db = lancedb.connect(self.db_path)
            # Create table if it doesn't exist
            if "documents" not in self.db.table_names():
                # Create initial schema
                initial_data = [{
                    "vector": self.embedding_model.encode("test").tolist(),
                    "text": "test",
                    "document_id": "init",
                    "document_name": "init",
                    "chunk_id": "init",
                    "page": 0,
                    "bbox": {}
                }]
                self.table = self.db.create_table("documents", initial_data)
                # Delete the initial record
                self.table.delete("document_id = 'init'")
            else:
                self.table = self.db.open_table("documents")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {str(e)}")
            raise VectorStoreError(f"Database initialization failed: {str(e)}")

    async def add_embeddings(self, chunks: List[Dict[str, Any]], document_id: str, document_name: str):
        """
        Add document chunks with embeddings to the vector store.

        Generates embeddings for each chunk and stores them with metadata.
        Each chunk is stored with position information for precise citations.

        Args:
            chunks: List of text chunks with metadata (text, page, bbox, chunk_id)
            document_id: Unique identifier for the document
            document_name: Human-readable document name

        Raises:
            VectorStoreError: If embedding generation or storage fails

        Example:
            ```python
            chunks = [
                {"text": "Machine learning is...", "page": 1, "bbox": {...}}
            ]
            await vector_service.add_embeddings(chunks, "doc123", "ML_Guide.pdf")
            ```
        """
        try:
            records = []
            for chunk in chunks:
                embedding = self.embedding_model.encode(chunk["text"])
                record = {
                    "vector": embedding.tolist(),
                    "text": chunk["text"],
                    "document_id": document_id,
                    "document_name": document_name,
                    "chunk_id": chunk.get("chunk_id", ""),
                    "page": chunk.get("page", 0),
                    "bbox": chunk.get("bbox", {})
                }
                records.append(record)

            if records:
                self.table.add(records)
                logger.info(f"Added {len(records)} chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to add embeddings: {str(e)}")
            raise VectorStoreError(f"Failed to add embeddings: {str(e)}")

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Perform semantic similarity search in the vector store.

        Encodes the query into a vector and finds similar documents
        using cosine similarity. Supports filtering by document IDs
        and minimum score thresholds.

        Args:
            query: SearchQuery with search text and parameters

        Returns:
            List of SearchResult objects sorted by similarity

        Raises:
            VectorStoreError: If search operation fails

        Example:
            ```python
            query = SearchQuery(query="machine learning", limit=5, min_score=0.7)
            results = await vector_service.search(query)
            ```
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query.query)

            # Perform search
            results = self.table.search(query_embedding.tolist()).limit(query.limit).to_list()

            # Filter by document IDs if specified
            if query.document_ids:
                results = [r for r in results if r["document_id"] in query.document_ids]

            # Convert to SearchResult objects
            search_results = []
            for result in results:
                # Calculate similarity score (cosine similarity)
                score = float(result.get("_distance", 0))
                if score >= query.min_score:
                    search_results.append(SearchResult(
                        text=result["text"],
                        document_id=result["document_id"],
                        document_name=result["document_name"],
                        score=score,
                        metadata=DocumentMetadata(
                            page=result.get("page"),
                            bbox=result.get("bbox"),
                            chunk_id=result.get("chunk_id", ""),
                            document_id=result["document_id"]
                        )
                    ))

            return search_results
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise VectorStoreError(f"Search failed: {str(e)}")

    async def delete_document(self, document_id: str):
        """
        Delete all chunks for a specific document.

        Removes all vector embeddings and metadata associated
        with the specified document from the database.

        Args:
            document_id: Document identifier to delete

        Raises:
            VectorStoreError: If deletion fails
        """
        try:
            self.table.delete(f"document_id = '{document_id}'")
            logger.info(f"Deleted all chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete document chunks: {str(e)}")
            raise VectorStoreError(f"Failed to delete document: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Provides insights into the database including:
        - Total number of unique documents
        - Total number of chunks
        - Embedding model being used
        - Database path

        Returns:
            Dictionary with database statistics

        Example:
            ```python
            stats = await vector_service.get_stats()
            # {"total_documents": 10, "total_chunks": 150, ...}
            ```
        """
        try:
            # Get unique document IDs
            all_records = self.table.to_pandas()
            unique_docs = all_records["document_id"].nunique()
            total_chunks = len(all_records)

            return {
                "total_documents": unique_docs,
                "total_chunks": total_chunks,
                "embedding_model": settings.embedding_model,
                "database_path": self.db_path
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {
                "error": str(e),
                "total_documents": 0,
                "total_chunks": 0
            }