from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class Usage(BaseModel):
    cost_cents: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    provider: str = ""
    model: str = ""
    latency_ms: int = 0


class LLMRequest(BaseModel):
    system: str | None = None
    user: str
    schema_: dict | None = None
    max_tokens: int = 2000
    temperature: float = 0.7


class LLMResult(BaseModel):
    text: str | None = None
    data: dict | None = None
    usage: Usage


class ImageRequest(BaseModel):
    prompt: str
    negative: str | None = None
    refs: list[str] = Field(default_factory=list)
    width: int = 1024
    height: int = 1024
    seed: int | None = None
    params: dict = Field(default_factory=dict)


class TTSRequest(BaseModel):
    text: str
    voice_id: str | None = None
    locale: str = "en"


class VideoRequest(BaseModel):
    prompt: str = ""
    refs: list[str] = Field(default_factory=list)
    width: int = 1080
    height: int = 1920
    duration_s: float = 8.0
    params: dict = Field(default_factory=dict)


class BinaryResult(BaseModel):
    data: bytes | None = None
    remote_url: str | None = None
    mime: str
    usage: Usage
    meta: dict = Field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    async def complete(self, req: LLMRequest) -> LLMResult: ...
    def estimate_cost(self, req: LLMRequest) -> int: ...


_REGISTRY: dict[str, dict[str, object]] = {
    "llm": {},
    "image": {},
    "tts": {},
    "video": {},
    "vision": {},
}


def register(kind: str, impl) -> None:
    _REGISTRY[kind][impl.name] = impl


def get(kind: str, name: str | None = None):
    from fcf.core.config import settings

    name = name or getattr(settings.providers, kind)
    try:
        return _REGISTRY[kind][name]
    except KeyError:
        raise LookupError(f"provider {kind}/{name} not registered")
