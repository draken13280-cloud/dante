from __future__ import annotations

import hashlib
import io

from PIL import Image, ImageDraw

from fcf.providers.base import BinaryResult, ImageRequest, Usage


class MockImage:
    name = "mock"

    def estimate_cost(self, req: ImageRequest) -> int:
        return 0

    async def generate(self, req: ImageRequest) -> BinaryResult:
        h = hashlib.sha256(req.prompt.encode()).hexdigest()
        base = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
        if hex_ := req.params.get("brand_hex"):
            hx = hex_.lstrip("#")
            base = tuple(int(hx[i : i + 2], 16) for i in (0, 2, 4))
        img = Image.new("RGB", (req.width, req.height), base)
        d = ImageDraw.Draw(img)
        for i in range(0, req.width, 64):
            d.line([(i, 0), (i, req.height)], fill=tuple(min(255, c + 12) for c in base))
        d.rectangle([40, 40, req.width - 40, req.height - 40], outline=(255, 255, 255), width=3)
        d.text((60, 60), f"MOCK\n{req.prompt[:60]}", fill=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return BinaryResult(
            data=buf.getvalue(),
            mime="image/png",
            usage=Usage(cost_cents=0, provider="mock", model="mock-image"),
            meta={"width": req.width, "height": req.height, "seed": req.seed},
        )
