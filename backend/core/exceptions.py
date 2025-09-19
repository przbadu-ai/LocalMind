"""
Exception handling for the FastAPI application.

This module defines custom exceptions and global exception handlers
to provide consistent error responses and logging throughout the API.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """
    Exception raised when document processing fails.

    Used for errors during:
    - File type detection
    - Text extraction
    - Chunking operations
    - PDF parsing
    - Image processing

    Example:
        ```python
        if not file_path.exists():
            raise DocumentProcessingError(f"File not found: {file_path}")
        ```
    """
    pass


class VectorStoreError(Exception):
    """
    Exception raised when vector store operations fail.

    Used for errors during:
    - Database connection
    - Embedding generation
    - Similarity search
    - Index operations
    - Data persistence

    Example:
        ```python
        try:
            self.db.connect()
        except Exception as e:
            raise VectorStoreError(f"Database connection failed: {e}")
        ```
    """
    pass


class LLMConnectionError(Exception):
    """
    Exception raised when LLM service is unavailable.

    Used for errors when:
    - Ollama server is unreachable
    - OpenAI API fails
    - Model loading fails
    - Response generation times out
    - API key is invalid

    Example:
        ```python
        if response.status_code != 200:
            raise LLMConnectionError("Ollama server not responding")
        ```
    """
    pass


def setup_exception_handlers(app: FastAPI):
    """
    Configure global exception handlers for consistent error responses.

    Registers handlers for:
    1. HTTP exceptions - Standard web errors
    2. Validation errors - Request/response validation
    3. Custom exceptions - Application-specific errors
    4. Unhandled exceptions - Catch-all for unexpected errors

    Args:
        app: FastAPI application instance

    Error Response Format:
        All errors return JSON with structure:
        ```json
        {
            "error": "Error message",
            "details": "Additional information",
            "status_code": 400
        }
        ```

    Logging:
        - All errors are logged with appropriate severity
        - Stack traces included for 500 errors
        - Request context preserved in logs
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Handle standard HTTP exceptions (404, 403, etc.).
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handle request validation errors.

        Provides detailed validation error information for debugging.
        """
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors()
            }
        )

    @app.exception_handler(DocumentProcessingError)
    async def document_exception_handler(request: Request, exc: DocumentProcessingError):
        """
        Handle document processing failures.

        Returns 400 Bad Request with details about the processing error.
        """
        logger.error(f"Document processing error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Document processing failed",
                "details": str(exc)
            }
        )

    @app.exception_handler(VectorStoreError)
    async def vector_store_exception_handler(request: Request, exc: VectorStoreError):
        """
        Handle vector database errors.

        Returns 500 Internal Server Error for database failures.
        """
        logger.error(f"Vector store error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Vector database error",
                "details": str(exc)
            }
        )

    @app.exception_handler(LLMConnectionError)
    async def llm_exception_handler(request: Request, exc: LLMConnectionError):
        """
        Handle LLM service unavailability.

        Returns 503 Service Unavailable when LLM cannot be reached.
        """
        logger.error(f"LLM connection error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "LLM service unavailable",
                "details": str(exc)
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Catch-all handler for unexpected exceptions.

        Logs full stack trace and returns generic error to client.
        """
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "details": "An unexpected error occurred"
            }
        )