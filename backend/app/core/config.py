
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "The Lenny Growth Assistant"
    app_version: str = "0.1.0"
    app_environment: str = "development"

    api_prefix: str = "/api"

    # Local Ollama configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: float = 90.0

    # Database configuration.
    # A local PostgreSQL instance can be configured later.
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/lenny_assistant"
    )

    # Comma-separated frontend origins.
    cors_origins: str = "http://localhost:5173"

    # Optional cloud provider key.
    anthropic_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
