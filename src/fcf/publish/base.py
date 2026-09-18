from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

from fcf.domain.enums import AssetKind


@dataclass(frozen=True)
class Capabilities:
    draft: bool
    live: bool
    kinds: frozenset[AssetKind]
    requires_public_url: bool
    auth: str
    max_video_s: int | None = None
    notes: str = ""


class PublishResult(BaseModel):
    status: str
    platform: str = ""
    external_id: str | None = None
    external_url: str | None = None
    error: str | None = None
    idempotency_key: str | None = None


class Publisher(Protocol):
    platform: str

    def capabilities(self) -> Capabilities: ...
    def configured(self) -> bool: ...
    async def publish(self, asset, copy, *, live: bool, idem: str) -> PublishResult: ...
