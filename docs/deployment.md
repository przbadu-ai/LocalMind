# LocalMind Deployment Guide

This guide covers deploying LocalMind to a server using [Kamal](https://kamal-deploy.org/), a deployment tool from 37signals (makers of Basecamp and HEY).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [GitHub Container Registry Setup](#github-container-registry-setup)
- [Server Setup](#server-setup)
- [Deployment Commands](#deployment-commands)
- [SSL Setup (Optional)](#ssl-setup-optional)
- [Troubleshooting](#troubleshooting)
  - [Backend deployment not picking up latest code](#6-backend-deployment-not-picking-up-latest-code)
  - [Server disk space full](#7-server-disk-space-full)
  - [Backend container shows "unhealthy" but API works](#8-backend-container-shows-unhealthy-but-api-works)
  - [MCP servers failing to start](#9-mcp-servers-failing-to-start-during-backend-startup)
- [Quick Reference: Manual Backend Deployment](#quick-reference-manual-backend-deployment)

## Prerequisites

### On Your Local Machine

1. **Ruby** (for Kamal gem)
   ```bash
   # macOS
   brew install ruby

   # Ubuntu/Debian
   sudo apt install ruby-full

   # Or use rbenv/rvm
   ```

2. **Docker** - Required for building images
   ```bash
   # Verify installation
   docker --version
   ```

3. **Kamal** - Install the deployment tool
   ```bash
   gem install kamal

   # Verify installation
   kamal version
   ```

### On Your Server

1. **Docker** - Must be installed and running
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```

2. **SSH Access** - Key-based authentication recommended
   ```bash
   # Copy your SSH key to the server
   ssh-copy-id root@your-server-ip
   ```

3. **Open Ports**
   - Port 3000 (or your configured port) for HTTP
   - Port 443 if using SSL

### External Services

1. **GitHub Account** - For container registry (ghcr.io)
2. **LLM Server** - Ollama, OpenAI, or compatible endpoint

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/przbadu/LocalMind.git
cd LocalMind

# 2. Copy and configure environment files
cp .env.example .env
cp .kamal/secrets.example .kamal/secrets

# 3. Edit .env with your values
#    - DEPLOY_SERVER_IP: Your server IP
#    - KAMAL_REGISTRY_PASSWORD: GitHub Personal Access Token
#    - LLM_API_KEY: Your LLM API key (or "not-required" for Ollama)

# 4. Edit config/deploy.yml if needed
#    - Update server IP
#    - Update registry username
#    - Adjust other settings as needed

# 5. First-time deployment
kamal setup

# 6. Subsequent deployments
kamal deploy
```

## One-Time Shell Configuration (Recommended)

To avoid loading environment variables before each deploy, add them to your shell profile:

```bash
# Add to ~/.bashrc or ~/.zshrc
export KAMAL_REGISTRY_PASSWORD="ghp_your_token_here"
export LLM_API_KEY="your_api_key_or_not-required"

# Reload your shell
source ~/.bashrc  # or source ~/.zshrc
```

After this setup, you can simply run:

```bash
kamal deploy
```

### Alternative: Load from .env file

If you prefer to keep secrets in .env file only, load them before deploying:

```bash
set -a && source .env && set +a && kamal deploy
```

Or create a convenient alias in your shell profile:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias kamal-deploy='set -a && source .env && set +a && kamal deploy'
alias kamal-setup='set -a && source .env && set +a && kamal setup'
```

## Configuration

### Environment Variables (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `DEPLOY_SERVER_IP` | Target server IP address | `192.168.1.100` |
| `DEPLOY_DOMAIN` | Domain name (optional) | - |
| `KAMAL_REGISTRY_PASSWORD` | GitHub PAT with `write:packages` | - |
| `LLM_PROVIDER` | LLM provider name | `ollama` |
| `LLM_BASE_URL` | LLM API endpoint | `http://192.168.1.173:11434/v1` |
| `LLM_API_KEY` | API key for LLM | `not-required` |
| `LLM_MODEL` | Default model | `llama3:instruct` |

### Kamal Configuration (config/deploy.yml)

Key sections to customize:

```yaml
# Service name (used for container naming)
service: localmind

# Docker image location
image: ghcr.io/your-username/localmind

# Target servers
servers:
  web:
    hosts:
      - your-server-ip

# Registry credentials
registry:
  server: ghcr.io
  username: your-github-username
  password:
    - KAMAL_REGISTRY_PASSWORD

# SSH user
ssh:
  user: root  # or your SSH user

# Backend accessory
accessories:
  backend:
    host: your-server-ip
    # ... other backend config
```

## GitHub Container Registry Setup

1. **Create a Personal Access Token (PAT)**
   - Go to [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens/new)
   - Or use this direct link: https://github.com/settings/tokens/new?scopes=write:packages
   - Select scopes: `write:packages`, `read:packages`, `delete:packages`
   - Generate and copy the token

2. **Configure the token**
   ```bash
   # Add to your .env file
   KAMAL_REGISTRY_PASSWORD=ghp_your_token_here
   ```

3. **Verify access**
   ```bash
   # Test login
   echo $KAMAL_REGISTRY_PASSWORD | docker login ghcr.io -u your-username --password-stdin
   ```

## Server Setup

### Automatic Setup (Recommended)

Kamal handles server setup automatically on first deployment:

```bash
kamal setup
```

This will:
- Install Docker if needed
- Configure Docker networks
- Set up the kamal-proxy
- Deploy your application

### Manual Server Preparation

If you prefer to set up the server manually:

```bash
# SSH into your server
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Create data directory
mkdir -p /var/data/localmind

# Ensure Docker is running
systemctl enable docker
systemctl start docker
```

### Ollama on Server

If running Ollama on the same server:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3:instruct

# Ollama runs on localhost:11434 by default
# The backend can access it via host.docker.internal:11434
```

## Deployment Commands

### Initial Setup

```bash
# First-time deployment (sets up everything)
kamal setup
```

### Regular Deployment

```bash
# Deploy latest changes
kamal deploy

# Deploy without running hooks
kamal deploy --skip-hooks
```

### Managing Services

```bash
# View running containers
kamal details

# View application logs
kamal app logs

# View backend logs
kamal accessory logs backend

# Follow logs in real-time
kamal app logs -f
```

### Rollback

```bash
# Rollback to previous version
kamal rollback

# Rollback to specific version
kamal rollback v1.2.3
```

### Maintenance

```bash
# Restart the application
kamal app boot

# Restart backend accessory
kamal accessory reboot backend

# Remove everything (WARNING: destructive)
kamal remove
```

### Debugging

```bash
# SSH into application container
kamal app exec -i bash

# SSH into backend container
kamal accessory exec backend -i bash

# View combined config (including resolved secrets)
kamal config
```

## SSL Setup (Optional)

### With a Domain Name

1. **Update DNS**
   - Point your domain to your server's IP address

2. **Update configuration**
   ```yaml
   # config/deploy.yml
   proxy:
     ssl: true
     host: your-domain.com
   ```

3. **Redeploy**
   ```bash
   kamal deploy
   ```

Kamal uses Let's Encrypt for automatic SSL certificate provisioning.

### Without a Domain (IP-based access)

SSL is not available for IP-based access. Access your app via:
```
http://your-server-ip:3000
```

## Troubleshooting

### Common Issues

#### 1. Docker build fails

```bash
# Check Docker is running
docker info

# Clear Docker cache and rebuild
kamal build push --no-cache
```

#### 2. Cannot connect to server

```bash
# Test SSH connection
ssh root@your-server-ip

# Verify SSH key is configured
ssh-add -l
```

#### 3. Registry authentication fails

```bash
# Test registry login manually
echo $KAMAL_REGISTRY_PASSWORD | docker login ghcr.io -u your-username --password-stdin

# Verify token has correct scopes
# Check at: https://github.com/settings/tokens
```

#### 4. Backend cannot connect to Ollama

```bash
# Verify Ollama is running on the server
curl http://localhost:11434/api/tags

# Check backend can reach host.docker.internal
kamal accessory exec backend -- curl http://host.docker.internal:11434/api/tags
```

#### 5. Database permission issues

```bash
# SSH into server and fix permissions
ssh root@your-server-ip
chmod -R 755 /var/data/localmind
```

### Useful Debug Commands

```bash
# View all containers
kamal app details

# Check accessory status
kamal accessory details backend

# View proxy logs
kamal proxy logs

# Check server Docker status
ssh root@your-server-ip "docker ps -a"
```

#### 6. Backend deployment not picking up latest code

**Symptoms:**
- `kamal deploy` succeeds but new code changes are not reflected
- Backend returns 404 for newly added endpoints
- Container image on server is outdated

**Root Cause:** Docker layer caching can cause stale images to be pushed even when code has changed.

**Diagnosis Steps:**

```bash
# 1. Check if endpoint exists in local code
grep -r "your_endpoint" backend/

# 2. Verify local Docker image has the new code
docker build -t test-backend ./backend
docker run --rm test-backend cat /app/api/chat.py | grep "your_endpoint"

# 3. Check what's running on the server
ssh root@192.168.1.173 "docker exec localmind-backend cat /app/api/chat.py | grep 'your_endpoint'"

# 4. Compare image IDs
docker images | grep localmind-backend
ssh root@192.168.1.173 "docker images | grep localmind-backend"
```

**Solution:**

```bash
# Rebuild the backend image with --no-cache to bust Docker cache
docker build --no-cache -t ghcr.io/przbadu/localmind-backend:latest ./backend

# Push the fresh image
docker push ghcr.io/przbadu/localmind-backend:latest

# On the server, pull the new image and restart
ssh root@192.168.1.173 "docker pull ghcr.io/przbadu/localmind-backend:latest && docker stop localmind-backend && docker rm localmind-backend"

# Re-run the container (use the same command from pre-deploy hook)
ssh root@192.168.1.173 "docker run -d \
  --name localmind-backend \
  --network kamal \
  --restart unless-stopped \
  --add-host host.docker.internal:host-gateway \
  -p 8001:8001 \
  -v /var/data/localmind:/app/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e PYTHONPATH=/app \
  -e DATABASE_PATH=/app/data/local_mind.db \
  -e 'OLLAMA_HOST=http://host.docker.internal:11434' \
  ghcr.io/przbadu/localmind-backend:latest \
  uvicorn main:app --host 0.0.0.0 --port 8001"

# Verify the endpoint is now available
ssh root@192.168.1.173 "curl -s http://localhost:8001/health"
```

#### 7. Server disk space full

**Symptoms:**
- `docker pull` fails with "no space left on device"
- Container builds fail

**Solution:**

```bash
# Clean up Docker resources on the server
ssh root@192.168.1.173 "docker system prune -af && docker volume prune -f"

# Verify space was reclaimed
ssh root@192.168.1.173 "df -h /"
```

#### 8. Backend container shows "unhealthy" but API works

**Symptoms:**
- `docker ps` shows the container as "unhealthy"
- But API endpoints (e.g., `/health`) respond correctly

**Cause:** The Dockerfile's HEALTHCHECK uses port 52817 but Kamal overrides the CMD to use port 8001. The Docker health check tries to connect to 52817 (the default) which doesn't exist.

**This is a cosmetic issue** - the application is functioning correctly. To verify:

```bash
# Test health endpoint directly
ssh root@192.168.1.173 "curl -s http://localhost:8001/health"

# Expected output: {"status":"healthy","version":"X.X.X","commit":"XXXXXX"}
```

**Note:** This will be fixed in a future update by aligning the Dockerfile HEALTHCHECK port with the Kamal configuration.

#### 9. MCP servers failing to start during backend startup

**Symptoms:**
- Backend logs show "Timeout connecting to MCP server X"
- "MCP servers: 0 started, N failed"

**Cause:** MCP servers require Docker images to be pulled on first run, which may timeout during the startup window.

**Solutions:**
1. **Pre-pull MCP Docker images on the server:**
   ```bash
   ssh root@192.168.1.173 "docker pull mcp/github:latest && docker pull mcp/postgres:latest && docker pull mcp/playwright:latest"
   ```

2. **Restart the backend after images are pulled:**
   ```bash
   ssh root@192.168.1.173 "docker restart localmind-backend"
   ```

3. **The MCP servers will auto-start once their images are available**

### Useful Debug Commands

```bash
# View all containers
kamal app details

# Check accessory status
kamal accessory details backend

# View proxy logs
kamal proxy logs

# Check server Docker status
ssh root@your-server-ip "docker ps -a"

# View backend container logs
ssh root@192.168.1.173 "docker logs localmind-backend --tail 100"

# Check what code is in the running container
ssh root@192.168.1.173 "docker exec localmind-backend ls -la /app"

# Verify API routes are registered
ssh root@192.168.1.173 "curl -s http://localhost:8001/openapi.json | head -200"
```

### Quick Reference: Manual Backend Deployment

If the normal `kamal deploy` doesn't update the backend, use this quick script:

```bash
#!/bin/bash
# Save as: bin/deploy-backend-manual

set -e
BACKEND_IMAGE="ghcr.io/przbadu/localmind-backend:latest"

echo "==> Building backend with --no-cache..."
docker build --no-cache -t "$BACKEND_IMAGE" ./backend

echo "==> Pushing to registry..."
docker push "$BACKEND_IMAGE"

echo "==> Deploying to server..."
ssh root@192.168.1.173 "
  docker pull $BACKEND_IMAGE
  docker stop localmind-backend 2>/dev/null || true
  docker rm localmind-backend 2>/dev/null || true
  docker run -d \
    --name localmind-backend \
    --network kamal \
    --restart unless-stopped \
    --add-host host.docker.internal:host-gateway \
    -p 8001:8001 \
    -v /var/data/localmind:/app/data \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e PYTHONPATH=/app \
    -e DATABASE_PATH=/app/data/local_mind.db \
    -e 'OLLAMA_HOST=http://host.docker.internal:11434' \
    $BACKEND_IMAGE \
    uvicorn main:app --host 0.0.0.0 --port 8001
"

echo "==> Waiting for health check..."
for i in {1..12}; do
    if ssh root@192.168.1.173 "curl -sf http://localhost:8001/health" > /dev/null 2>&1; then
        echo "==> Backend is healthy!"
        exit 0
    fi
    echo "  Waiting... (attempt $i/12)"
    sleep 5
done

echo "==> Backend deployed but health check timed out (may still be starting)"
```

### Getting Help

- [Kamal Documentation](https://kamal-deploy.org/docs/)
- [Kamal GitHub Issues](https://github.com/basecamp/kamal/issues)
- [LocalMind GitHub Issues](https://github.com/przbadu/LocalMind/issues)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Server                                │
│  ┌─────────────┐     ┌──────────────────────────────────┐   │
│  │ kamal-proxy │────▶│ localmind (nginx + React)        │   │
│  │   :3000     │     │              :80                  │   │
│  └─────────────┘     └──────────────┬───────────────────┘   │
│                                      │                       │
│                                      ▼                       │
│                      ┌──────────────────────────────────┐   │
│                      │ localmind-backend (FastAPI)      │   │
│                      │              :52817               │   │
│                      └──────────────┬───────────────────┘   │
│                                      │                       │
│                                      ▼                       │
│                      ┌──────────────────────────────────┐   │
│                      │ /var/data/localmind (SQLite DB)  │   │
│                      └──────────────────────────────────┘   │
│                                      │                       │
│                                      ▼                       │
│                      ┌──────────────────────────────────┐   │
│                      │ host.docker.internal:11434       │   │
│                      │ (Ollama on host)                 │   │
│                      └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```
