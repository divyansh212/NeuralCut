"""Centralized config. Reads from environment / .env."""

from __future__ import annotations
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # mode
    provider_mode: str = Field(default="mock")  # mock | live

    # supabase
    supabase_url: str = Field(default="", alias="NEXT_PUBLIC_SUPABASE_URL")
    supabase_anon_key: str = Field(default="", alias="NEXT_PUBLIC_SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_db_url: str = Field(default="postgresql://postgres:postgres@db:5432/postgres")

    # storage buckets
    assets_bucket: str = "veedra-assets"
    renders_bucket: str = "veedra-renders"

    # redis / celery
    redis_url: str = "redis://redis:6379/0"

    # llm
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-5"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # image
    image_provider: str = "replicate"
    replicate_api_token: str = ""
    stability_api_key: str = ""

    # tts
    tts_provider: str = "elevenlabs"
    elevenlabs_api_key: str = ""

    # local fallback when supabase storage is not configured
    local_storage_dir: str = "/tmp/veedra"


@lru_cache
def get_settings() -> Settings:
    return Settings()
