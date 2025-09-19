"""
Centralized configuration for the entire application.

This is the single source of truth for all configuration settings.
No other files should define these values.
"""

import os
from pathlib import Path
from typing import Optional

# =============================================================================
# ENVIRONMENT
# =============================================================================
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
APP_NAME = "Local Mind"
APP_VERSION = "0.1.0"

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================
# Backend API Server
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 52817
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"
API_PREFIX = "/api/v1"

# Frontend Development Server
FRONTEND_URL = "http://localhost:3000"
TAURI_URL = "tauri://localhost"
TAURI_DEV_URL = "http://localhost:1420"

# =============================================================================
# LLM CONFIGURATION
# =============================================================================
# Ollama Configuration (Primary)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "192.168.1.173")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:latest")

# LlamaCpp Configuration (Alternative)
LLAMACPP_HOST = os.getenv("LLAMACPP_HOST", "localhost")
LLAMACPP_PORT = os.getenv("LLAMACPP_PORT", "8000")
LLAMACPP_BASE_URL = f"http://{LLAMACPP_HOST}:{LLAMACPP_PORT}"
LLAMACPP_MODEL = os.getenv("LLAMACPP_MODEL", "model.gguf")

# OpenAI Configuration (Alternative)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Active LLM Provider
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # Options: ollama, llamacpp, openai

# =============================================================================
# EMBEDDING CONFIGURATION
# =============================================================================
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

# =============================================================================
# DOCUMENT PROCESSING
# =============================================================================
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

# =============================================================================
# VECTOR DATABASE
# =============================================================================
VECTOR_DB_TYPE = "lancedb"  # We're using LanceDB exclusively
SIMILARITY_TOP_K = 5  # Number of similar documents to retrieve

# =============================================================================
# CORS CONFIGURATION
# =============================================================================
CORS_ORIGINS = [
    FRONTEND_URL,
    TAURI_URL,
    TAURI_DEV_URL,
    f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",  # Allow Ollama server
]

# Additional allowed hosts (comma-separated in env)
ADDITIONAL_HOSTS = os.getenv("ADDITIONAL_HOSTS", "").split(",")
for host in ADDITIONAL_HOSTS:
    if host.strip():
        CORS_ORIGINS.append(f"http://{host.strip()}")

# =============================================================================
# DATA DIRECTORIES
# =============================================================================
def get_data_directory() -> Path:
    """Get platform-specific data directory."""
    import platform

    system = platform.system()
    if system == "Windows":
        base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    elif system == "Darwin":  # macOS
        base_dir = Path.home() / "Library" / "Application Support"
    else:  # Linux and others
        base_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))

    data_dir = base_dir / APP_NAME / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

DATA_DIR = get_data_directory()
LANCEDB_DIR = DATA_DIR / "lancedb"
UPLOADS_DIR = DATA_DIR / "uploads"
LOGS_DIR = DATA_DIR / "logs"

# Create all directories
for directory in [DATA_DIR, LANCEDB_DIR, UPLOADS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_llm_config():
    """Get the active LLM configuration based on provider."""
    if LLM_PROVIDER == "ollama":
        return {
            "provider": "ollama",
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
            "api_key": None
        }
    elif LLM_PROVIDER == "llamacpp":
        return {
            "provider": "llamacpp",
            "base_url": LLAMACPP_BASE_URL,
            "model": LLAMACPP_MODEL,
            "api_key": None
        }
    elif LLM_PROVIDER == "openai":
        return {
            "provider": "openai",
            "base_url": "https://api.openai.com",
            "model": OPENAI_MODEL,
            "api_key": OPENAI_API_KEY
        }
    else:
        # Default to Ollama
        return {
            "provider": "ollama",
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
            "api_key": None
        }

def get_openai_base_url():
    """Get the OpenAI-compatible API base URL for the current provider."""
    config = get_llm_config()
    base_url = config["base_url"]

    # Add /v1 suffix for OpenAI compatibility if not already present
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"

    return base_url

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# =============================================================================
# EXPORT ALL CONFIGURATION
# =============================================================================
__all__ = [
    # Environment
    "DEBUG", "APP_NAME", "APP_VERSION",

    # Server
    "BACKEND_HOST", "BACKEND_PORT", "BACKEND_URL", "API_PREFIX",
    "FRONTEND_URL", "TAURI_URL", "TAURI_DEV_URL",

    # LLM
    "OLLAMA_HOST", "OLLAMA_PORT", "OLLAMA_BASE_URL", "OLLAMA_MODEL",
    "LLAMACPP_HOST", "LLAMACPP_PORT", "LLAMACPP_BASE_URL", "LLAMACPP_MODEL",
    "OPENAI_API_KEY", "OPENAI_MODEL",
    "LLM_PROVIDER",

    # Embeddings
    "EMBEDDING_MODEL", "EMBEDDING_DIMENSION",

    # Document Processing
    "CHUNK_SIZE", "CHUNK_OVERLAP", "MAX_FILE_SIZE_MB",

    # Vector DB
    "VECTOR_DB_TYPE", "SIMILARITY_TOP_K",

    # CORS
    "CORS_ORIGINS",

    # Directories
    "DATA_DIR", "LANCEDB_DIR", "UPLOADS_DIR", "LOGS_DIR",

    # Helper Functions
    "get_llm_config", "get_openai_base_url", "get_data_directory",

    # Logging
    "LOG_LEVEL", "LOG_FORMAT"
]

if __name__ == "__main__":
    # Print configuration for debugging
    print("=" * 60)
    print("LOCAL MIND CONFIGURATION")
    print("=" * 60)
    print(f"Debug Mode: {DEBUG}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Prefix: {API_PREFIX}")
    print("-" * 60)
    print(f"LLM Provider: {LLM_PROVIDER}")
    print(f"LLM Config: {get_llm_config()}")
    print(f"OpenAI API URL: {get_openai_base_url()}")
    print("-" * 60)
    print(f"Data Directory: {DATA_DIR}")
    print(f"LanceDB Directory: {LANCEDB_DIR}")
    print(f"Uploads Directory: {UPLOADS_DIR}")
    print("-" * 60)
    print(f"CORS Origins: {CORS_ORIGINS}")
    print("=" * 60)