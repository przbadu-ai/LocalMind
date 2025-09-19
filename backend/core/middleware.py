from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from config import settings
import time
from fastapi import Request


def setup_middlewares(app: FastAPI):
    """Configure all middleware for the FastAPI application."""

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

    # Trusted host middleware
    # Combine default hosts with additional hosts from settings
    allowed_hosts = ["localhost", "127.0.0.1", "*.tauri.localhost"]
    if settings.additional_allowed_hosts:
        allowed_hosts.extend(settings.additional_allowed_hosts)

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

    # Custom timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    return app