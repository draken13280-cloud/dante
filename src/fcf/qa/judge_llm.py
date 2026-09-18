from fcf.domain.enums import Severity
from fcf.providers.base import LLMRequest
from fcf.providers.call import call_provider
from fcf.qa.engine import QACheck

JUDGE_SCHEMA = {
    "type": "object",
    "required": ["tone_match", "factual", "issues"],
    "properties": {
        "tone_match": {"type": "number"},
        "factual": {"type": "boolean"},
        "issues": {"type": "array"},
    },
}


async def judge_copy(content, product, brand, ctx) -> list[QACheck]:
    res = await call_provider(
        "llm",
        "complete",
        LLMRequest(
            system=None,
            user=f"BRAND VOICE: {brand.tone.voice}\nFACTS: {product.model_dump()}\nCOPY: {content}",
            schema_=JUDGE_SCHEMA,
            temperature=0.0,
        ),
        ctx=ctx,
    )
    d = res.data or {"tone_match": 0.8, "factual": True, "issues": []}
    return [
        QACheck(
            "tone_match_llm",
            d.get("tone_match", 0) >= 0.7,
            Severity.MAJOR,
            float(d.get("tone_match", 0)),
            f"tone score {d.get('tone_match', 0):.2f}",
            "Rewrite closer to brand voice.",
        ),
        QACheck(
            "factual_llm",
            bool(d.get("factual", True)),
            Severity.BLOCKER,
            float(bool(d.get("factual", True))),
            "unsupported claims",
            "Only state facts from the product data.",
        ),
    ]
