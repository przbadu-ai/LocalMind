"""
Database models for Local Mind application.

This module defines the SQLAlchemy ORM models for storing:
- Chat conversations
- Messages with user/assistant roles
- Document references and citations
- User preferences and settings
"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Float, Boolean, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from pathlib import Path
from config.app_settings import DATA_DIR

# Create base class for models
Base = declarative_base()

# Database path
DB_PATH = Path(DATA_DIR) / "localmind.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Create engine
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def generate_uuid():
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class Chat(Base):
    """
    Represents a chat conversation.

    A chat contains multiple messages and maintains metadata
    about the conversation context and settings.
    """
    __tablename__ = "chats"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Chat settings
    model = Column(String(100), default="llama3:instruct")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    system_prompt = Column(Text)

    # Chat metadata
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime(timezone=True))
    is_archived = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    tags = Column(JSON, default=list)  # Array of tag strings

    # Relationships
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_chat_updated', 'updated_at'),
        Index('idx_chat_archived', 'is_archived'),
        Index('idx_chat_pinned', 'is_pinned'),
    )


class Message(Base):
    """
    Represents a single message in a chat.

    Messages can be from users or assistants, and may include
    references to documents and citations.
    """
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    chat_id = Column(String, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Message metadata
    tokens_used = Column(Integer)
    processing_time_ms = Column(Integer)
    error_message = Column(Text)
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime(timezone=True))

    # RAG-specific fields
    context_used = Column(JSON)  # Array of document chunks used
    citations = Column(JSON)  # Array of citation objects
    confidence_score = Column(Float)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    references = relationship("MessageReference", back_populates="message", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_message_chat', 'chat_id'),
        Index('idx_message_created', 'created_at'),
        Index('idx_message_role', 'role'),
    )


class Document(Base):
    """
    Represents a document in the knowledge base.

    Documents are processed and chunked for use in RAG.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(50))  # pdf, docx, txt, md, etc.
    file_size = Column(Integer)  # Size in bytes
    file_hash = Column(String(64))  # SHA256 hash for deduplication

    # Document metadata
    title = Column(String(255))
    author = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)

    # Content and chunks
    full_text = Column(Text)
    chunk_count = Column(Integer, default=0)
    doc_metadata = Column("metadata", JSON)  # Additional document metadata (column name is 'metadata' in DB)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    references = relationship("MessageReference", back_populates="document")

    # Indexes
    __table_args__ = (
        Index('idx_document_hash', 'file_hash'),
        Index('idx_document_status', 'status'),
        Index('idx_document_type', 'file_type'),
    )


class DocumentChunk(Base):
    """
    Represents a chunk of a document for RAG processing.

    Each chunk contains text, embeddings, and position information.
    """
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document

    # Content
    text = Column(Text, nullable=False)
    tokens = Column(Integer)

    # Position tracking for highlighting
    page_number = Column(Integer)
    bbox = Column(JSON)  # {"x0": 0, "y0": 0, "x1": 100, "y1": 100}
    start_char = Column(Integer)
    end_char = Column(Integer)

    # Vector embedding (stored as JSON array for SQLite)
    embedding = Column(JSON)
    embedding_model = Column(String(100))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index('idx_chunk_document', 'document_id'),
        Index('idx_chunk_index', 'chunk_index'),
    )


class MessageReference(Base):
    """
    Links messages to document references.

    Tracks which documents/chunks were referenced in a message.
    """
    __tablename__ = "message_references"

    id = Column(String, primary_key=True, default=generate_uuid)
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    # Reference details
    reference_type = Column(String(50))  # 'citation', 'context', 'source'
    chunk_ids = Column(JSON)  # Array of chunk IDs used
    relevance_score = Column(Float)
    highlight_text = Column(Text)  # Specific text being referenced

    # Position in message
    start_position = Column(Integer)  # Character position in message
    end_position = Column(Integer)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("Message", back_populates="references")
    document = relationship("Document", back_populates="references")

    # Indexes
    __table_args__ = (
        Index('idx_reference_message', 'message_id'),
        Index('idx_reference_document', 'document_id'),
    )


class UserPreference(Base):
    """
    Stores user preferences and settings.

    Key-value store for user-specific configuration.
    """
    __tablename__ = "user_preferences"

    key = Column(String(100), primary_key=True)
    value = Column(JSON)
    category = Column(String(50))  # 'ui', 'model', 'processing', etc.
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_preference_category', 'category'),
    )


def init_database():
    """Initialize the database and create all tables."""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DB_PATH}")


def get_db():
    """
    Get a database session.

    This is a dependency that can be used in FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Export commonly used items
__all__ = [
    "Base",
    "Chat",
    "Message",
    "Document",
    "DocumentChunk",
    "MessageReference",
    "UserPreference",
    "engine",
    "SessionLocal",
    "get_db",
    "init_database",
    "generate_uuid"
]