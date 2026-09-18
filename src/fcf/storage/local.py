from __future__ import annotations

import json
from pathlib import Path


class LocalStore:
    def __init__(self, root: str | Path = "/tmp/fcf-assets"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        key = key.replace("://", "/").lstrip("/")
        p = self.root / key
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        p = self._path(key)
        p.write_bytes(data)
        return f"file://{p}"

    async def put_json(self, key: str, obj: dict) -> str:
        p = self._path(key)
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2))
        return f"file://{p}"

    async def get(self, uri: str) -> bytes:
        path = uri.removeprefix("file://")
        return Path(path).read_bytes()

    async def exists(self, uri: str) -> bool:
        path = str(uri).removeprefix("file://")
        return Path(path).exists() if path else False

    async def presign_public(self, uri: str, ttl_s: int = 3600) -> str:
        return uri
