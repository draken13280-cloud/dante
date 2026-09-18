from __future__ import annotations

import hashlib

from fcf.domain.assets import AssetRef
from fcf.domain.brand import BrandKit
from fcf.domain.enums import AssetKind
from fcf.domain.plan import AssetSpec
from fcf.domain.product import Product
from fcf.providers.base import LLMRequest
from fcf.providers.call import call_provider

COPY_SCHEMA = {
    "type": "object",
    "required": ["title", "body", "hashtags", "cta", "alt_text", "script"],
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"},
        "bullets": {"type": "array", "items": {"type": "string"}},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "cta": {"type": "string"},
        "alt_text": {"type": "string"},
        "script": {"type": "string"},
        "seo": {"type": "object"},
    },
}


async def generate_copy(
    spec: AssetSpec, product: Product, brand: BrandKit, ctx, feedback: list[str] | None = None
) -> AssetRef:
    pol = brand.channels[spec.channel]
    constraints = [
        f"title: max {pol.title_max} characters",
        f"body: max {pol.body_max} characters",
        f"hashtags: exactly {pol.hashtags_min}-{pol.hashtags_max}",
        f"emoji: max {pol.emoji_max}",
        f"reading level: grade {brand.tone.reading_level_max} or lower",
        "CTA required" if pol.cta_required else "no hard CTA",
        f"never mention: {', '.join(brand.tone.banned_phrases + brand.claims.forbid_competitor_mentions)}",
        f"material is exactly: {product.attrs.material}. Do not imply any other fibre.",
        f"colour is exactly: {product.attrs.color}.",
        f"ASSET_KEY={spec.key}",
    ]
    if not product.attrs.certifications:
        constraints.append("Do NOT make any sustainability or eco claim.")
    if not product.attrs.on_promo:
        constraints.append("Do NOT mention discounts, sales or price.")
    user = (spec.prompt.user if spec.prompt else product.title) + "\n\nCONSTRAINTS:\n- " + "\n- ".join(
        constraints
    )
    if feedback:
        user += "\n\nPREVIOUS ATTEMPT FAILED QA. Fix exactly these issues:\n- " + "\n- ".join(feedback)
    res = await call_provider(
        "llm",
        "complete",
        LLMRequest(
            system=f"Brand voice: {brand.tone.voice}",
            user=user,
            schema_=COPY_SCHEMA,
            temperature=0.6 if feedback else 0.85,
        ),
        ctx=ctx,
        provider_name=spec.provider,
    )
    uri = await ctx.store.put_json(f"{ctx.prefix}/{spec.key}.json", res.data)
    return AssetRef(
        key=spec.key,
        kind=AssetKind.COPY,
        channel=spec.channel,
        uri=uri,
        content=res.data,
        meta={
            "model": res.usage.model,
            "cost_cents": res.usage.cost_cents,
            "prompt_hash": hashlib.sha1(user.encode()).hexdigest(),
        },
    )
