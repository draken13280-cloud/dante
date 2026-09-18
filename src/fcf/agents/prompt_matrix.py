from __future__ import annotations

from fcf.core.ids import asset_key
from fcf.domain.brand import BrandKit
from fcf.domain.enums import AssetKind, Channel
from fcf.domain.plan import AssetSpec, ContentPlan, PromptSet
from fcf.domain.product import Product
from fcf.providers.base import LLMRequest
from fcf.providers.call import call_provider

PLAN_SCHEMA = {
    "type": "object",
    "required": ["concept", "assets"],
    "properties": {
        "concept": {"type": "string"},
        "assets": {"type": "array", "items": {"type": "object"}},
    },
}

TEMPLATES = {
    Channel.SHOPIFY: "Write a Shopify product title and body for {title}. Material {attrs}.",
    Channel.TIKTOK: "Write a TikTok caption and VO script for {title}.",
    Channel.IG_REEL: "Write an Instagram Reel caption for {title}.",
    Channel.IG_POST: "Write an Instagram post caption for {title}.",
    Channel.EMAIL: "Write an email teaser for {title}.",
}


async def build_plan(product: Product, brand: BrandKit, channels: list[Channel], ctx) -> ContentPlan:
    try:
        res = await call_provider(
            "llm",
            "complete",
            LLMRequest(
                system=f"You are creative director for {brand.name}. Voice: {brand.tone.voice}",
                user=f"{product.title} {product.attrs.model_dump()}",
                schema_=PLAN_SCHEMA,
                temperature=0.8,
            ),
            ctx=ctx,
        )
        plan = _plan_from_llm(res.data or {}, product, brand, channels)
        if plan.specs:
            return plan
    except Exception as e:
        await ctx.emit("prompt_matrix.fallback", error=str(e))
    return deterministic_plan(product, brand, channels)


def _plan_from_llm(data: dict, product, brand, channels) -> ContentPlan:
    # LLM plan is advisory; we still emit a complete deterministic skeleton.
    return deterministic_plan(product, brand, channels)


def deterministic_plan(product: Product, brand: BrandKit, channels: list[Channel]) -> ContentPlan:
    specs: list[AssetSpec] = []
    for ch in channels:
        pol = brand.channels[ch]
        tmpl = TEMPLATES.get(ch, TEMPLATES[Channel.SHOPIFY])
        user = tmpl.format(title=product.title, attrs=product.attrs.model_dump())
        specs.append(
            AssetSpec(
                key=asset_key(AssetKind.COPY, ch, "a"),
                kind=AssetKind.COPY,
                channel=ch,
                prompt=PromptSet(user=user),
            )
        )
        specs.append(
            AssetSpec(
                key=asset_key(AssetKind.COPY, ch, "b"),
                kind=AssetKind.COPY,
                channel=ch,
                variant="b",
                prompt=PromptSet(user=user, params={"angle": "benefit"}),
            )
        )
        specs.append(
            AssetSpec(
                key=asset_key(AssetKind.IMAGE, ch, "hero"),
                kind=AssetKind.IMAGE,
                channel=ch,
                variant="hero",
                prompt=PromptSet(
                    user=(
                        f"editorial studio photo of {product.title}, "
                        f"{product.attrs.color} {product.attrs.material}, "
                        f"neutral background, soft key light"
                    ),
                    negative="text, watermark, extra limbs, distorted hands",
                    refs=[str(u) for u in product.source_images[:1]],
                    params={"brand_hex": product.attrs.color_hex},
                ),
            )
        )
        if pol.duration_s:
            specs.append(
                AssetSpec(
                    key=asset_key(AssetKind.AUDIO, ch),
                    kind=AssetKind.AUDIO,
                    channel=ch,
                    depends_on=[asset_key(AssetKind.COPY, ch, "a")],
                )
            )
            specs.append(
                AssetSpec(
                    key=asset_key(AssetKind.VIDEO, ch),
                    kind=AssetKind.VIDEO,
                    channel=ch,
                    depends_on=[
                        asset_key(AssetKind.IMAGE, ch, "hero"),
                        asset_key(AssetKind.AUDIO, ch),
                    ],
                )
            )
    return ContentPlan(specs=specs, concept="deterministic fallback")
