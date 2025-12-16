"""Settings API endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings
from database.repositories.config_repository import ConfigRepository
from services.llm_service import llm_service

router = APIRouter()

config_repo = ConfigRepository()


class LLMSettingsRequest(BaseModel):
    """Request body for updating LLM settings."""

    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None


class LLMSettingsResponse(BaseModel):
    """Response model for LLM settings."""

    provider: str
    base_url: str
    api_key: str  # Masked
    model: str
    available: bool


class SettingsResponse(BaseModel):
    """Response model for all settings."""

    llm: LLMSettingsResponse
    app: dict


def _mask_api_key(api_key: str) -> str:
    """Mask API key for display."""
    if not api_key or api_key == "not-required":
        return api_key
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]


@router.get("/settings")
async def get_settings() -> SettingsResponse:
    """Get all settings."""
    # Get LLM settings from database or use defaults
    llm_config = config_repo.get_config_value("llm", {})

    return SettingsResponse(
        llm=LLMSettingsResponse(
            provider=llm_config.get("provider", settings.llm_provider),
            base_url=llm_config.get("base_url", settings.llm_base_url),
            api_key=_mask_api_key(llm_config.get("api_key", settings.llm_api_key)),
            model=llm_config.get("model", settings.llm_model),
            available=llm_service.is_available(),
        ),
        app={
            "name": "Local Mind",
            "version": "0.1.0",
            "database_path": str(settings.database_full_path),
        },
    )


@router.get("/settings/llm")
async def get_llm_settings() -> LLMSettingsResponse:
    """Get LLM settings."""
    llm_config = config_repo.get_config_value("llm", {})

    return LLMSettingsResponse(
        provider=llm_config.get("provider", settings.llm_provider),
        base_url=llm_config.get("base_url", settings.llm_base_url),
        api_key=_mask_api_key(llm_config.get("api_key", settings.llm_api_key)),
        model=llm_config.get("model", settings.llm_model),
        available=llm_service.is_available(),
    )


@router.put("/settings/llm")
async def update_llm_settings(request: LLMSettingsRequest) -> LLMSettingsResponse:
    """Update LLM settings."""
    # Get current settings
    current = config_repo.get_config_value("llm", {
        "provider": settings.llm_provider,
        "base_url": settings.llm_base_url,
        "api_key": settings.llm_api_key,
        "model": settings.llm_model,
    })

    # Update with new values
    if request.provider is not None:
        current["provider"] = request.provider
    if request.base_url is not None:
        current["base_url"] = request.base_url
    if request.api_key is not None:
        current["api_key"] = request.api_key
    if request.model is not None:
        current["model"] = request.model

    # Save to database
    config_repo.set_config("llm", current, category="llm")

    # Update the global LLM service
    llm_service.update_config(
        base_url=current["base_url"],
        api_key=current["api_key"],
        model=current["model"],
    )

    return LLMSettingsResponse(
        provider=current["provider"],
        base_url=current["base_url"],
        api_key=_mask_api_key(current["api_key"]),
        model=current["model"],
        available=llm_service.is_available(),
    )


@router.get("/settings/llm/models")
async def get_available_models() -> dict:
    """Get list of available models from the LLM provider."""
    models = llm_service.get_models()

    return {
        "models": models,
        "current_model": llm_service.model,
        "available": len(models) > 0,
    }


@router.get("/settings/llm/health")
async def check_llm_health() -> dict:
    """Check LLM service health."""
    available = llm_service.is_available()

    return {
        "available": available,
        "base_url": llm_service.base_url,
        "model": llm_service.model,
        "message": "LLM service is available" if available else "Cannot connect to LLM service",
    }


@router.post("/settings/llm/test")
async def test_llm_connection(request: LLMSettingsRequest) -> dict:
    """Test LLM connection with provided settings."""
    from services.llm_service import LLMService, ChatMessage

    # Use provided settings or current ones
    llm_config = config_repo.get_config_value("llm", {})

    test_service = LLMService(
        base_url=request.base_url or llm_config.get("base_url", settings.llm_base_url),
        api_key=request.api_key or llm_config.get("api_key", settings.llm_api_key),
        model=request.model or llm_config.get("model", settings.llm_model),
    )

    try:
        # Try to get models first (lighter test)
        models = test_service.get_models()
        if models:
            return {
                "success": True,
                "message": f"Connected successfully. Found {len(models)} models.",
                "models": models[:10],  # Return first 10 models
            }

        # If no models returned, try a simple chat
        response = test_service.chat(
            [ChatMessage(role="user", content="Hello")],
            max_tokens=10,
        )

        return {
            "success": True,
            "message": "Connected successfully.",
            "models": [],
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "models": [],
        }


@router.get("/settings/config/{key}")
async def get_config_value(key: str) -> dict:
    """Get a specific configuration value."""
    config = config_repo.get_config(key)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return {
        "key": config.key,
        "value": config.value,
        "category": config.category,
    }


@router.put("/settings/config/{key}")
async def set_config_value(key: str, value: dict[str, Any], category: str = "general") -> dict:
    """Set a configuration value."""
    config = config_repo.set_config(key, value, category)

    return {
        "key": config.key,
        "value": config.value,
        "category": config.category,
    }


@router.delete("/settings/config/{key}")
async def delete_config_value(key: str) -> dict:
    """Delete a configuration value."""
    if not config_repo.delete_config(key):
        raise HTTPException(status_code=404, detail="Configuration not found")

    return {"success": True, "message": f"Configuration '{key}' deleted"}
