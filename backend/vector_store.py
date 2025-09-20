"""
LanceDB Vector Store for Local Mind
Handles document embeddings storage and similarity search
"""

import os
import lancedb
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path
import pyarrow as pa
from config.app_settings import LANCE_DB_PATH, DEFAULT_EMBEDDING_MODEL

class VectorStore:
    """LanceDB vector store for document embeddings"""

    def __init__(self, db_path: str = LANCE_DB_PATH):
        """Initialize the vector store"""
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Connect to LanceDB
        self.db = lancedb.connect(str(self.db_path))

        # Initialize tables
        self._init_tables()

    def _init_tables(self):
        """Initialize database tables"""
        # Documents table schema
        document_schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("content", pa.string()),
            pa.field("embedding", pa.list_(pa.float32(), 384)),  # all-MiniLM-L6-v2 has 384 dimensions
            pa.field("metadata", pa.string()),  # JSON string
            pa.field("document_id", pa.string()),
            pa.field("chunk_id", pa.string()),
            pa.field("page", pa.int32()),
            pa.field("bbox", pa.string()),  # JSON string for bounding box
            pa.field("file_path", pa.string()),
            pa.field("file_name", pa.string()),
            pa.field("created_at", pa.timestamp('ms')),
            pa.field("updated_at", pa.timestamp('ms'))
        ])

        # Create tables if they don't exist
        table_names = self.db.table_names()

        if "documents" not in table_names:
            # Create empty table with schema
            self.documents_table = self.db.create_table(
                "documents",
                data=[],
                schema=document_schema
            )
        else:
            self.documents_table = self.db.open_table("documents")

        # Sources table for tracking indexed files
        if "sources" not in table_names:
            sources_schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("path", pa.string()),
                pa.field("name", pa.string()),
                pa.field("type", pa.string()),  # 'file' or 'folder'
                pa.field("size", pa.int64()),
                pa.field("file_count", pa.int32()),
                pa.field("status", pa.string()),  # 'pending', 'processing', 'completed', 'error'
                pa.field("error", pa.string()),
                pa.field("last_indexed", pa.timestamp('ms')),
                pa.field("created_at", pa.timestamp('ms'))
            ])

            self.sources_table = self.db.create_table(
                "sources",
                data=[],
                schema=sources_schema
            )
        else:
            self.sources_table = self.db.open_table("sources")

    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add documents to the vector store

        Args:
            documents: List of document dictionaries with keys:
                - content: Document text content
                - embedding: Embedding vector
                - metadata: Additional metadata
                - document_id: Unique document identifier
                - chunk_id: Chunk identifier
                - page: Page number (optional)
                - bbox: Bounding box coordinates (optional)
                - file_path: Path to source file
                - file_name: Name of source file

        Returns:
            List of document IDs
        """
        if not documents:
            return []

        # Prepare data for insertion
        data = []
        doc_ids = []

        for doc in documents:
            doc_id = doc.get('id', f"doc_{datetime.now().timestamp()}_{len(data)}")
            doc_ids.append(doc_id)

            # Convert metadata to JSON string
            metadata = json.dumps(doc.get('metadata', {}))
            bbox = json.dumps(doc.get('bbox', {})) if doc.get('bbox') else None

            data.append({
                "id": doc_id,
                "content": doc['content'],
                "embedding": doc['embedding'],
                "metadata": metadata,
                "document_id": doc.get('document_id', ''),
                "chunk_id": doc.get('chunk_id', ''),
                "page": doc.get('page', 0),
                "bbox": bbox,
                "file_path": doc.get('file_path', ''),
                "file_name": doc.get('file_name', ''),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })

        # Add to table
        self.documents_table.add(data)

        return doc_ids

    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        return_with_distance: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_dict: Optional filters to apply
            return_with_distance: Whether to return distance scores

        Returns:
            List of similar documents with metadata
        """
        # Build search query
        results = self.documents_table.search(query_embedding).limit(k)

        # Apply filters if provided
        if filter_dict:
            for key, value in filter_dict.items():
                if key in ['document_id', 'file_path', 'file_name']:
                    results = results.where(f"{key} = '{value}'")

        # Execute search
        results_df = results.to_pandas()

        # Format results
        documents = []
        for _, row in results_df.iterrows():
            doc = {
                'id': row['id'],
                'content': row['content'],
                'document_id': row['document_id'],
                'chunk_id': row['chunk_id'],
                'page': row['page'],
                'file_path': row['file_path'],
                'file_name': row['file_name'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                'bbox': json.loads(row['bbox']) if row['bbox'] else None
            }

            if return_with_distance:
                doc['distance'] = row.get('_distance', 0.0)

            documents.append(doc)

        return documents

    def delete_documents(self, document_ids: List[str]) -> int:
        """
        Delete documents by their IDs

        Args:
            document_ids: List of document IDs to delete

        Returns:
            Number of documents deleted
        """
        if not document_ids:
            return 0

        # LanceDB doesn't have direct delete yet, so we filter and recreate
        # This is a workaround until delete is supported
        existing_data = self.documents_table.to_pandas()
        filtered_data = existing_data[~existing_data['id'].isin(document_ids)]

        # Drop and recreate table with filtered data
        self.db.drop_table("documents")

        if not filtered_data.empty:
            self.documents_table = self.db.create_table("documents", filtered_data)
        else:
            # Recreate empty table with schema
            self._init_tables()

        return len(document_ids)

    def delete_by_file_path(self, file_path: str) -> int:
        """
        Delete all documents from a specific file

        Args:
            file_path: Path to the file

        Returns:
            Number of documents deleted
        """
        existing_data = self.documents_table.to_pandas()
        filtered_data = existing_data[existing_data['file_path'] != file_path]

        num_deleted = len(existing_data) - len(filtered_data)

        # Drop and recreate table with filtered data
        self.db.drop_table("documents")

        if not filtered_data.empty:
            self.documents_table = self.db.create_table("documents", filtered_data)
        else:
            self._init_tables()

        return num_deleted

    def add_source(self, source_info: Dict[str, Any]) -> str:
        """
        Add a source file or folder to track

        Args:
            source_info: Source information dictionary

        Returns:
            Source ID
        """
        source_id = source_info.get('id', f"src_{datetime.now().timestamp()}")

        data = {
            'id': source_id,
            'path': source_info['path'],
            'name': source_info['name'],
            'type': source_info.get('type', 'file'),
            'size': source_info.get('size', 0),
            'file_count': source_info.get('file_count', 1),
            'status': source_info.get('status', 'pending'),
            'error': source_info.get('error', ''),
            'last_indexed': datetime.now() if source_info.get('status') == 'completed' else None,
            'created_at': datetime.now()
        }

        self.sources_table.add([data])
        return source_id

    def update_source_status(self, source_id: str, status: str, error: str = ""):
        """Update the status of a source"""
        # Get existing data
        existing_data = self.sources_table.to_pandas()

        # Update the specific source
        existing_data.loc[existing_data['id'] == source_id, 'status'] = status
        existing_data.loc[existing_data['id'] == source_id, 'error'] = error
        if status == 'completed':
            existing_data.loc[existing_data['id'] == source_id, 'last_indexed'] = datetime.now()

        # Recreate table with updated data
        self.db.drop_table("sources")
        self.sources_table = self.db.create_table("sources", existing_data)

    def get_sources(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all sources, optionally filtered by status"""
        df = self.sources_table.to_pandas()

        if status:
            df = df[df['status'] == status]

        sources = []
        for _, row in df.iterrows():
            sources.append({
                'id': row['id'],
                'path': row['path'],
                'name': row['name'],
                'type': row['type'],
                'size': row['size'],
                'file_count': row['file_count'],
                'status': row['status'],
                'error': row['error'],
                'last_indexed': row['last_indexed'].isoformat() if row['last_indexed'] else None,
                'created_at': row['created_at'].isoformat()
            })

        return sources

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        num_documents = len(self.documents_table.to_pandas())
        num_sources = len(self.sources_table.to_pandas())

        sources_df = self.sources_table.to_pandas()
        sources_by_status = sources_df['status'].value_counts().to_dict() if not sources_df.empty else {}

        return {
            'total_documents': num_documents,
            'total_sources': num_sources,
            'sources_by_status': sources_by_status,
            'db_path': str(self.db_path),
            'embedding_model': DEFAULT_EMBEDDING_MODEL
        }

    def clear_all(self):
        """Clear all data from the vector store"""
        self.db.drop_table("documents")
        self.db.drop_table("sources")
        self._init_tables()