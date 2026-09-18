from __future__ import annotations

import uuid

from fcf.domain.enums import AssetKind, Channel


def new_id(prefix: str = "") -> str:
    uid = uuid.uuid4().hex[:16]
    return f"{prefix}{uid}" if prefix else uid


def asset_key(
    kind: AssetKind | str,
    channel: Channel | str,
    variant: str = "a",
    locale: str = "en",
) -> str:
    k = kind.value if hasattr(kind, "value") else kind
    c = channel.value if hasattr(channel, "value") else channel
    return f"{k}:{c}:{variant}:{locale}"
