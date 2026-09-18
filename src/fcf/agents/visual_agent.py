from __future__ import annotations

from fcf.domain.assets import AssetRef
from fcf.domain.enums import AssetKind
from fcf.domain.plan import AssetSpec
from fcf.providers.base import ImageRequest
from fcf.providers.call import call_provider


async def generate_image_only(spec: AssetSpec, ctx, feedback=None) -> AssetRef:
    prompt = spec.prompt.user if spec.prompt else "product photo"
    params = spec.prompt.params if spec.prompt else {}
    pol = ctx.brand.channels[spec.channel]
    w = max(pol.min_width, 1024)
    h = w
    if pol.aspect == "9:16":
        h = int(w * 16 / 9)
    elif pol.aspect == "4:5":
        h = int(w * 5 / 4)
    res = await call_provider(
        "image",
        "generate",
        ImageRequest(
            prompt=prompt + ((" Fix: " + "; ".join(feedback)) if feedback else ""),
            negative=spec.prompt.negative if spec.prompt else None,
            refs=spec.prompt.refs if spec.prompt else [],
            width=w,
            height=h,
            params=params,
        ),
        ctx=ctx,
        provider_name=spec.provider,
    )
    uri = await ctx.store.put(f"{ctx.prefix}/{spec.key}.png", res.data or b"", "image/png")
    meta = dict(res.meta)
    meta.setdefault("width", w)
    meta.setdefault("height", h)
    return AssetRef(key=spec.key, kind=AssetKind.IMAGE, channel=spec.channel, uri=uri, meta=meta)
