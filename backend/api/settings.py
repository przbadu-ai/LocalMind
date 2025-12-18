"""Settings API endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings
from database.models import LLMProvider
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
    is_default: bool = False


class LLMProviderResponse(BaseModel):
    """Response model for a single LLM provider."""

    name: str
    base_url: str
    api_key: str  # Masked
    model: str
    is_default: bool


class LLMProvidersListResponse(BaseModel):
    """Response model for list of LLM providers."""

    providers: list[LLMProviderResponse]
    default_provider: Optional[str]


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


def _get_default_provider_settings() -> dict:
    """Get the default provider settings or fall back to config."""
    default_provider = config_repo.get_default_llm_provider()
    if default_provider:
        return {
            "provider": default_provider.name,
            "base_url": default_provider.base_url,
            "api_key": default_provider.api_key or "",
            "model": default_provider.model or "",
            "is_default": True,
        }
    # Fall back to old config system for backward compatibility
    llm_config = config_repo.get_config_value("llm", {})
    return {
        "provider": llm_config.get("provider", settings.llm_provider),
        "base_url": llm_config.get("base_url", settings.llm_base_url),
        "api_key": llm_config.get("api_key", settings.llm_api_key),
        "model": llm_config.get("model", settings.llm_model),
        "is_default": True,
    }


@router.get("/settings")
async def get_settings() -> SettingsResponse:
    """Get all settings."""
    provider_settings = _get_default_provider_settings()

    return SettingsResponse(
        llm=LLMSettingsResponse(
            provider=provider_settings["provider"],
            base_url=provider_settings["base_url"],
            api_key=_mask_api_key(provider_settings["api_key"]),
            model=provider_settings["model"],
            available=llm_service.is_available(),
            is_default=provider_settings["is_default"],
        ),
        app={
            "name": "Local Mind",
            "version": "0.1.0",
            "database_path": str(settings.database_full_path),
        },
    )


@router.get("/settings/llm")
async def get_llm_settings() -> LLMSettingsResponse:
    """Get LLM settings (returns default provider)."""
    provider_settings = _get_default_provider_settings()

    return LLMSettingsResponse(
        provider=provider_settings["provider"],
        base_url=provider_settings["base_url"],
        api_key=_mask_api_key(provider_settings["api_key"]),
        model=provider_settings["model"],
        available=llm_service.is_available(),
        is_default=provider_settings["is_default"],
    )


@router.put("/settings/llm")
async def update_llm_settings(request: LLMSettingsRequest) -> LLMSettingsResponse:
    """Update LLM settings (updates/creates provider and sets as default)."""
    provider_name = request.provider or settings.llm_provider

    # Get existing provider or create new
    existing = config_repo.get_llm_provider(provider_name)

    if existing:
        # Update existing provider
        if request.base_url is not None:
            existing.base_url = request.base_url
        if request.api_key is not None:
            existing.api_key = request.api_key
        if request.model is not None:
            existing.model = request.model
        existing.is_default = True
        provider = config_repo.update_llm_provider(existing)
    else:
        # Create new provider
        provider = LLMProvider(
            name=provider_name,
            base_url=request.base_url or settings.llm_base_url,
            api_key=request.api_key,
            model=request.model,
            is_default=True,
        )
        provider = config_repo.create_llm_provider(provider)

    # Set as default (unsets others)
    config_repo.set_default_llm_provider(provider_name)

    # Also update old config for backward compatibility
    config_repo.set_config("llm", {
        "provider": provider.name,
        "base_url": provider.base_url,
        "api_key": provider.api_key or "",
        "model": provider.model or "",
    }, category="llm")

    # Update the global LLM service
    llm_service.update_config(
        base_url=provider.base_url,
        api_key=provider.api_key,
        model=provider.model,
    )

    return LLMSettingsResponse(
        provider=provider.name,
        base_url=provider.base_url,
        api_key=_mask_api_key(provider.api_key or ""),
        model=provider.model or "",
        available=llm_service.is_available(),
        is_default=True,
    )


# New provider-specific endpoints

@router.get("/settings/llm/providers")
async def get_llm_providers() -> LLMProvidersListResponse:
    """Get all saved LLM providers."""
    providers = config_repo.get_all_llm_providers()
    default = config_repo.get_default_llm_provider()

    return LLMProvidersListResponse(
        providers=[
            LLMProviderResponse(
                name=p.name,
                base_url=p.base_url,
                api_key=_mask_api_key(p.api_key or ""),
                model=p.model or "",
                is_default=p.is_default,
            )
            for p in providers
        ],
        default_provider=default.name if default else None,
    )


@router.get("/settings/llm/providers/{name}")
async def get_llm_provider(name: str) -> LLMProviderResponse:
    """Get a specific LLM provider by name."""
    provider = config_repo.get_llm_provider(name)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found")

    return LLMProviderResponse(
        name=provider.name,
        base_url=provider.base_url,
        api_key=_mask_api_key(provider.api_key or ""),
        model=provider.model or "",
        is_default=provider.is_default,
    )


@router.put("/settings/llm/providers/{name}")
async def update_llm_provider(name: str, request: LLMSettingsRequest) -> LLMProviderResponse:
    """Create or update a specific LLM provider."""
    existing = config_repo.get_llm_provider(name)

    if existing:
        # Update existing
        if request.base_url is not None:
            existing.base_url = request.base_url
        if request.api_key is not None:
            existing.api_key = request.api_key
        if request.model is not None:
            existing.model = request.model
        provider = config_repo.update_llm_provider(existing)
    else:
        # Create new
        provider = LLMProvider(
            name=name,
            base_url=request.base_url or "",
            api_key=request.api_key,
            model=request.model,
            is_default=False,
        )
        provider = config_repo.create_llm_provider(provider)

    return LLMProviderResponse(
        name=provider.name,
        base_url=provider.base_url,
        api_key=_mask_api_key(provider.api_key or ""),
        model=provider.model or "",
        is_default=provider.is_default,
    )


@router.delete("/settings/llm/providers/{name}")
async def delete_llm_provider(name: str) -> dict:
    """Delete an LLM provider."""
    if not config_repo.delete_llm_provider(name):
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found")

    return {"success": True, "message": f"Provider '{name}' deleted"}


@router.post("/settings/llm/providers/{name}/default")
async def set_default_llm_provider(name: str) -> LLMProviderResponse:
    """Set a provider as the default."""
    provider = config_repo.get_llm_provider(name)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found")

    config_repo.set_default_llm_provider(name)

    # Also update old config for backward compatibility
    config_repo.set_config("llm", {
        "provider": provider.name,
        "base_url": provider.base_url,
        "api_key": provider.api_key or "",
        "model": provider.model or "",
    }, category="llm")

    # Update the global LLM service
    llm_service.update_config(
        base_url=provider.base_url,
        api_key=provider.api_key,
        model=provider.model,
    )

    # Refresh provider to get updated is_default
    provider = config_repo.get_llm_provider(name)

    return LLMProviderResponse(
        name=provider.name,
        base_url=provider.base_url,
        api_key=_mask_api_key(provider.api_key or ""),
        model=provider.model or "",
        is_default=provider.is_default,
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
                "models": models,
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


@router.post("/settings/llm/models")
async def fetch_available_models(request: LLMSettingsRequest) -> dict:
    """Fetch available models based on provided settings."""
    from services.llm_service import LLMService

    # Use provided settings or current ones
    llm_config = config_repo.get_config_value("llm", {})

    service = LLMService(
        base_url=request.base_url or llm_config.get("base_url", settings.llm_base_url),
        api_key=request.api_key or llm_config.get("api_key", settings.llm_api_key),
        model=request.model or llm_config.get("model", settings.llm_model),
    )

    try:
        models = service.get_models()
        return {
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        return {
            "models": [],
            "error": str(e)
        }

