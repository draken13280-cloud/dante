from __future__ import annotations

import asyncio

from fcf.core.config import settings
from fcf.domain.assets import AssetRef
from fcf.domain.enums import AssetKind, Channel
from fcf.publish.base import PublishResult
from fcf.publish.instagram import InstagramPublisher
from fcf.publish.shopify import ShopifyPublisher
from fcf.publish.tiktok import TikTokPublisher
from fcf.publish.youtube import YouTubePublisher

PUBLISHERS = {
    "shopify": ShopifyPublisher(),
    "tiktok": TikTokPublisher(),
    "instagram_reel": InstagramPublisher(),
    "instagram_post": InstagramPublisher(),
    "youtube_shorts": YouTubePublisher(),
}


async def _static(platform, status, error) -> PublishResult:
    return PublishResult(status=status, platform=platform, error=error)


def _copy_for(state, ch) -> dict:
    from fcf.core.ids import asset_key

    a = state.get("assets", {}).get(asset_key(AssetKind.COPY, ch, "a")) or {}
    return a.get("content") or {}


def _publishable(state, ch, kinds):
    out = []
    for key, asset in (state.get("assets") or {}).items():
        if f":{ch}:" not in f":{key}:":
            continue
        kind = asset.get("kind")
        if kind in {k.value for k in kinds} or (isinstance(kind, AssetKind) and kind in kinds):
            out.append((key, asset))
    return out


async def dispatch_publish(state, ctx) -> list[dict]:
    live_allowed = settings.allow_live_publish and state.get("mode") == "live"
    extra = state.get("extra_platforms") or []
    channels = list(state.get("channels") or []) + extra
    results: list[PublishResult] = []
    for ch in channels:
        pub = PUBLISHERS.get(ch)
        if not pub:
            results.append(await _static(ch, "unsupported", "no publisher implemented"))
            continue
        caps = pub.capabilities()
        if not pub.configured():
            results.append(await _static(ch, "unsupported" if ch == "youtube_shorts" else "skipped", caps.notes))
            continue
        items = _publishable(state, ch, caps.kinds)
        if not items:
            results.append(await _static(ch, "skipped", "no matching assets"))
            continue
        for key, asset in items:
            verdict = (state.get("qa") or {}).get(key, {}).get("verdict", "pass")
            if verdict == "fail":
                results.append(await _static(ch, "skipped", f"QA failed for {key}"))
                continue
            uri = asset.get("uri")
            if caps.requires_public_url:
                uri = await ctx.store.presign_public(uri, ttl_s=3600)
            want_live = live_allowed and caps.live
            idem = f"{state['job_id']}:{ch}:{key}:{'live' if want_live else 'draft'}"
            try:
                r = await pub.publish(
                    AssetRef(**{**asset, "uri": uri}),
                    _copy_for(state, ch),
                    live=want_live,
                    idem=idem,
                )
            except Exception as e:
                r = PublishResult(status="failed", platform=ch, error=f"{type(e).__name__}: {e}")
            await ctx.persist_publish(state["job_id"], ch, r)
            await ctx.emit("publish.attempt", platform=ch, status=r.status, error=r.error)
            results.append(r)
    return [r.model_dump() for r in results]
