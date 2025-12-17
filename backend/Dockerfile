# Backend Dockerfile for Local Mind
# Python FastAPI backend with LLM chat and YouTube transcription
# Supports both Docker Compose and Kamal deployments

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

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
