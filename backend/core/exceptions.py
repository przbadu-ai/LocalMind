from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Raised when document processing fails."""
    pass


class VectorStoreError(Exception):
    """Raised when vector store operations fail."""
    pass


class LLMConnectionError(Exception):
    """Raised when LLM service is unavailable."""
    pass


def setup_exception_handlers(app: FastAPI):
    """Configure global exception handlers."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors()
            }
        )

    @app.exception_handler(DocumentProcessingError)
    async def document_exception_handler(request: Request, exc: DocumentProcessingError):
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
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "details": "An unexpected error occurred"
            }
        )