import lancedb
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from config import settings
from core.exceptions import VectorStoreError
from models.schemas import SearchQuery, SearchResult, DocumentMetadata
import logging

logger = logging.getLogger(__name__)


class VectorService:
    """Service for managing vector embeddings and similarity search."""

    def __init__(self):
        self.db_path = str(settings.lancedb_dir)
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.db = None
        self.table = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize LanceDB connection."""
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
        """Add document chunks with embeddings to the vector store."""
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
        """Perform similarity search in the vector store."""
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
        """Delete all chunks for a specific document."""
        try:
            self.table.delete(f"document_id = '{document_id}'")
            logger.info(f"Deleted all chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete document chunks: {str(e)}")
            raise VectorStoreError(f"Failed to delete document: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
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