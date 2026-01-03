# Backend Dockerfile for Local Mind
# Python FastAPI backend with LLM chat and YouTube transcription
# Supports both Docker Compose and Kamal deployments
#
# Uses pre-built base image with heavy dependencies (docling, PyTorch, etc.)
# To rebuild base image: ./scripts/build-base-image.sh

FROM ghcr.io/przbadu/localmind-base:latest

# Build arguments for version info
ARG APP_VERSION=0.0.0-dev
ARG GIT_COMMIT=unknown

# Set environment variables
ENV PYTHONPATH=/app
ENV APP_VERSION=${APP_VERSION}
ENV GIT_COMMIT=${GIT_COMMIT}

# Copy requirements and install remaining (lightweight) dependencies
COPY requirements.txt .

# Install only the dependencies not already in base image
# This is fast since heavy deps (docling, pydantic-ai, openai) are pre-installed
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create VERSION file with build-time version
RUN echo "${APP_VERSION}" > /app/VERSION

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Expose port
EXPOSE 52817

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:52817/health || exit 1

# Run the application (production mode - no reload)
# Can be overridden by Kamal's cmd configuration
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "52817"]
