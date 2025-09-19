from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List
import os


class Settings(BaseSettings):
    # App settings - read from environment variables
    app_name: str = os.getenv("APP_NAME", "Local Mind")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # API settings
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    cors_origins: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:1420,tauri://localhost"
    ).split(",")

    # Additional allowed hosts (for proxmox server, etc.)
    additional_allowed_hosts: List[str] = os.getenv(
        "ADDITIONAL_ALLOWED_HOSTS",
        ""
    ).split(",") if os.getenv("ADDITIONAL_ALLOWED_HOSTS") else []

    # Database settings
    data_dir: Path = Path(os.getenv("DATA_DIR", Path(__file__).parent.parent.parent / "data"))
    lancedb_dir: Path = Path(os.getenv("LANCEDB_DIR", data_dir / "lancedb"))
    uploads_dir: Path = Path(os.getenv("UPLOADS_DIR", data_dir / "uploads"))

    # Model settings
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    default_llm_model: str = os.getenv("DEFAULT_LLM_MODEL", "ollama:llama2")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Document processing
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "512"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.lancedb_dir.mkdir(exist_ok=True, parents=True)
        self.uploads_dir.mkdir(exist_ok=True, parents=True)


settings = Settings()