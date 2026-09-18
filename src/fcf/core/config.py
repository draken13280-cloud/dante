from enum import StrEnum

from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Mode(StrEnum):
    MOCK = "mock"
    LIVE = "live"


class ProviderSel(BaseModel):
    llm: str = "mock"
    image: str = "mock"
    tts: str = "mock"
    video: str = "mock"
    vision: str = "mock"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore"
    )

    mode: Mode = Mode.MOCK
    providers: ProviderSel = ProviderSel()

    database_url: str = "postgresql+asyncpg://fcf:fcf@postgres:5432/fcf"
    redis_url: str = "redis://redis:6379/0"

    s3_endpoint: str = "http://minio:9000"
    s3_bucket: str = "fcf-assets"
    s3_public_bucket: str = "fcf-public"
    s3_key: str = "minio"
    s3_secret: str = "minio12345"

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    replicate_api_token: str | None = None
    elevenlabs_api_key: str | None = None
    runway_api_key: str | None = None

    default_budget_cents: int = 250
    max_regen_per_asset: int = 2
    max_total_regens: int = 6
    provider_concurrency: int = 4
    node_timeout_s: int = 600

    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    ffmpeg_timeout_s: int = 300

    allow_live_publish: bool = False
    approval_required_default: bool = True

    langsmith_tracing: bool = False

    @model_validator(mode="after")
    def _guard_live(self):
        if self.mode is Mode.LIVE:
            need = {
                "anthropic": self.anthropic_api_key,
                "openai": self.openai_api_key,
                "replicate_flux": self.replicate_api_token,
                "elevenlabs": self.elevenlabs_api_key,
                "runway": self.runway_api_key,
            }
            for name in self.providers.model_dump().values():
                if name != "mock" and name in need and not need[name]:
                    raise ValueError(f"LIVE mode: missing credentials for {name}")
        return self


settings = Settings()
