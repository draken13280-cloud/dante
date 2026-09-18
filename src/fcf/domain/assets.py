from pydantic import BaseModel, Field

from fcf.domain.enums import AssetKind, Channel


class AssetMeta(BaseModel):
    width: int | None = None
    height: int | None = None
    duration_s: float | None = None
    model: str | None = None
    prompt_hash: str | None = None
    cost_cents: int = 0
    extra: dict = Field(default_factory=dict)


class AssetRef(BaseModel):
    key: str
    kind: AssetKind
    channel: Channel | None = None
    uri: str
    content: dict | None = None
    meta: dict = Field(default_factory=dict)
    local_path: str | None = None
