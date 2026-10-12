
from fastapi import APIRouter
import httpx

from app.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    settings = get_settings()

    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health/ready")
async def readiness():
    settings = get_settings()

    ollama_status = "available"
    ollama_models: list[str] = []

    try:
        async with httpx.AsyncClient(
            timeout=5.0
        ) as client:
            response = await client.get(
                f"{settings.ollama_base_url.rstrip('/')}/api/tags"
            )
            response.raise_for_status()
            data = response.json()

        ollama_models = [
            model.get("name", "")
            for model in data.get("models", [])
        ]

    except (httpx.HTTPError, ValueError):
        ollama_status = "unavailable"

    return {
        "status": "ready" if ollama_status == "available" else "degraded",
        "dependencies": {
            "ollama": ollama_status,
        },
        "ollama_models": ollama_models,
        "configured_model": settings.ollama_model,
    }
