"""
Middleware configuration for the FastAPI application.

This module sets up all middleware layers including:
- CORS (Cross-Origin Resource Sharing) for Tauri integration
- Trusted host validation for security
- Request timing for performance monitoring
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from config import app_config
import time
from fastapi import Request


def setup_middlewares(app: FastAPI):
    """
    Configure all middleware layers for the FastAPI application.

    Sets up a middleware stack that handles:
    1. CORS - Enables cross-origin requests from Tauri frontend
    2. Trusted Hosts - Validates incoming host headers for security
    3. Timing - Adds response time headers for monitoring

    Args:
        app: FastAPI application instance to configure

    Middleware Order (important):
    1. CORS (must be early to handle preflight requests)
    2. TrustedHost (security validation)
    3. Custom middleware (timing, logging, etc.)

    Security Notes:
    - CORS is configured for Tauri's specific origins
    - Only specific HTTP methods are allowed
    - Host validation prevents host header injection
    """

    # CORS middleware - Configure cross-origin resource sharing
    # Required for Tauri frontend to communicate with backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.CORS_ORIGINS,  # Tauri origins
        allow_credentials=True,  # Allow cookies/auth headers
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # RESTful methods
        allow_headers=["*"],  # Accept all headers from client
    )

    # Trusted host middleware - Validate Host header
    # Prevents host header injection attacks
    allowed_hosts = ["localhost", "127.0.0.1", "*.tauri.localhost"]

    # Add additional hosts from configuration
    for origin in app_config.CORS_ORIGINS:
        # Extract host from URL
        if "://" in origin:
            host = origin.split("://")[1].split(":")[0]
            if host not in allowed_hosts:
                allowed_hosts.append(host)

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

    # Custom timing middleware - Add response time tracking
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """
        Add X-Process-Time header to all responses.

        Measures the time taken to process each request and adds it
        as a custom header for performance monitoring.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with added timing header

        Header Format:
            X-Process-Time: 0.123 (time in seconds)
        """
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    return app