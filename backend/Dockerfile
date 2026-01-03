# Backend Dockerfile for Local Mind
# Python FastAPI backend with LLM chat and YouTube transcription
# Supports both Docker Compose and Kamal deployments

FROM python:3.11-slim

# Build arguments for version info
ARG APP_VERSION=0.0.0-dev
ARG GIT_COMMIT=unknown

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV APP_VERSION=${APP_VERSION}
ENV GIT_COMMIT=${GIT_COMMIT}

# Set working directory
WORKDIR /app

# Install system dependencies including Docker CLI for Docker-based MCP servers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with pip cache for faster rebuilds
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
