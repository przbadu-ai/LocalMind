# Frontend Dockerfile for Local Mind
# React frontend served via nginx
# Supports both Docker Compose and Kamal deployments

# Build stage
FROM node:20-slim AS builder

# Build arguments for version info
ARG APP_VERSION=0.0.0-dev
ARG GIT_COMMIT=unknown

# Install bun
RUN npm install -g bun

WORKDIR /app

# Copy package files
COPY package.json bun.lock* ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source code (excluding backend via .dockerignore)
COPY src/ ./src/
COPY public/ ./public/
COPY index.html ./
COPY vite.config.ts ./
COPY tsconfig*.json ./
COPY tailwind.config.ts ./
COPY postcss.config.js ./
COPY components.json ./

# Create a Docker-specific app.config.json with empty API base URL
# This allows the frontend to use relative URLs, which nginx proxies to backend
RUN echo '{ \
  "app": { "name": "Local Mind", "version": "0.1.0", "description": "AI chat application" }, \
  "backend": { "host": "0.0.0.0", "port": 52817, "api_base_url": "", "cors_origins": ["*"] }, \
  "models": { \
    "embedding": { "default": "all-MiniLM-L6-v2", "options": ["all-MiniLM-L6-v2"] }, \
    "llm": { \
      "provider": "ollama", "default_model": "llama3:instruct", \
      "ollama": { "host": "localhost", "port": 11434, "base_url": "http://localhost:11434", "models": [] }, \
      "openai": { "base_url": "https://api.openai.com/v1", "models": [] }, \
      "llamacpp": { "host": "localhost", "port": 8080, "base_url": "http://localhost:8080" } \
    } \
  }, \
  "storage": { "data_dir": "./data", "database_path": "./data/local_mind.db" }, \
  "features": { "enable_youtube": true, "enable_mcp": true, "enable_offline_mode": true } \
}' > app.config.json

# Set version environment variables for Vite build
ENV VITE_APP_VERSION=${APP_VERSION}
ENV VITE_GIT_COMMIT=${GIT_COMMIT}
ENV VITE_BUILD_TIME=${BUILD_TIME}

# Build the frontend only (web mode, not Tauri)
RUN bun run build:frontend

# Production stage
FROM nginx:alpine

# Copy nginx config template and entrypoint script
COPY docker/nginx.conf.template /etc/nginx/templates/nginx.conf.template
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Environment variables for backend configuration
# These can be overridden at runtime
ENV BACKEND_HOST=localmind-backend
ENV BACKEND_PORT=52817

# Expose port
EXPOSE 80

# Health check - uses the /up endpoint for Kamal compatibility
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/up || exit 1

# Use custom entrypoint to substitute env vars in nginx config
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
