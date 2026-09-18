from __future__ import annotations

from fcf.core.ids import asset_key
from fcf.domain.assets import AssetRef
from fcf.domain.enums import AssetKind
from fcf.domain.plan import AssetSpec
from fcf.providers.base import VideoRequest
from fcf.providers.call import call_provider


async def generate_video(spec: AssetSpec, ctx, feedback=None) -> AssetRef:
    pol = ctx.brand.channels[spec.channel]
    lo, hi = pol.duration_s or (9, 30)
    audio = ctx.assets.get(asset_key(AssetKind.AUDIO, spec.channel))
    dur = lo
    if audio:
        dur = min(hi, max(lo, float(audio.get("meta", {}).get("duration_s", lo) or lo) + 1.0))
    image = ctx.assets.get(asset_key(AssetKind.IMAGE, spec.channel, "hero"))
    refs = [image["uri"]] if image else []
    res = await call_provider(
        "video",
        "generate",
        VideoRequest(
            prompt=(spec.prompt.user if spec.prompt else "product film"),
            refs=refs,
            width=1080,
            height=1920,
            duration_s=dur,
        ),
        ctx=ctx,
        provider_name=spec.provider,
    )
    uri = await ctx.store.put(f"{ctx.prefix}/{spec.key}.mp4", res.data or b"", "video/mp4")
    return AssetRef(key=spec.key, kind=AssetKind.VIDEO, channel=spec.channel, uri=uri, meta=res.meta)
