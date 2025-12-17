# Frontend Dockerfile for Local Mind
# React frontend served via nginx

# Build stage
FROM node:20-slim AS builder

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
COPY tailwind.config.js ./
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

# Build the frontend (web mode, not Tauri)
RUN bun run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
