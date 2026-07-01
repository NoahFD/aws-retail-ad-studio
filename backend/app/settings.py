from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:5174,"
    "http://127.0.0.1:5174,"
    "http://localhost:5175,"
    "http://127.0.0.1:5175,"
    "http://localhost:5176,"
    "http://127.0.0.1:5176"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_max_output_tokens: int = 700
    openai_image_model: str = "gpt-image-2"
    openai_image_size: str | None = None
    openai_image_quality: str = "low"
    image_provider: str = "gpt-image-2"
    aws_bedrock_image_model: str = "bedrock-image-adapter"
    video_provider: str = "seedance-ark"
    video_live_enabled: bool = True
    ark_api_key: str | None = None
    seedance_base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3"
    seedance_model: str = "dreamina-seedance-2-0-fast-260128"
    seedance_ratio: str = "9:16"
    seedance_resolution: str = "480p"
    seedance_duration_seconds: int = 4
    seedance_poll_seconds: int = 18
    aws_region: str = "us-east-1"
    aws_nova_reel_model: str = "amazon.nova-reel-v1:1"
    aws_nova_reel_s3_uri: str | None = None
    backend_cors_origins: str = DEFAULT_CORS_ORIGINS

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
