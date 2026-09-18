from __future__ import annotations

import re

from fcf.domain.assets import AssetRef
from fcf.domain.enums import AssetKind
from fcf.domain.plan import AssetSpec
from fcf.providers.base import TTSRequest
from fcf.providers.call import call_provider


def _strip_unspeakable(script: str) -> str:
    script = re.sub(r"#\w+", "", script)
    script = re.sub(r"https?://\S+", "", script)
    script = re.sub(r"[\U0001F300-\U0001FAFF]", "", script)
    return " ".join(script.split())


async def generate_audio_only(spec: AssetSpec, ctx, feedback=None) -> AssetRef:
    dep = spec.depends_on[0] if spec.depends_on else None
    content = (ctx.assets.get(dep) or {}).get("content") or {}
    script = _strip_unspeakable(content.get("script") or content.get("body") or "built to last")
    res = await call_provider(
        "tts",
        "generate",
        TTSRequest(text=script, locale=spec.locale),
        ctx=ctx,
        provider_name=spec.provider,
    )
    uri = await ctx.store.put(f"{ctx.prefix}/{spec.key}.wav", res.data or b"", "audio/wav")
    return AssetRef(
        key=spec.key,
        kind=AssetKind.AUDIO,
        channel=spec.channel,
        uri=uri,
        meta=res.meta,
    )
