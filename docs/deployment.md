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
