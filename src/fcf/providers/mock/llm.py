from __future__ import annotations

import json
import re

from fcf.providers.base import LLMRequest, LLMResult, Usage


class MockLLM:
    name = "mock"
    fault_injection: dict[str, str] = {}

    def estimate_cost(self, req: LLMRequest) -> int:
        return 0

    async def complete(self, req: LLMRequest) -> LLMResult:
        schema = req.schema_ or {}
        required = schema.get("required") or []
        if "title" in required or "body" in required:
            data = self._copy(req)
        elif "concept" in required or "assets" in required:
            data = {"concept": "indigo denim, cut for movement", "assets": []}
        elif "tone_match" in required:
            data = {"tone_match": 0.85, "factual": True, "issues": []}
        else:
            data = {"text": req.user[:200]}
        return LLMResult(
            text=json.dumps(data),
            data=data,
            usage=Usage(provider="mock", model="mock-llm"),
        )

    def _copy(self, req: LLMRequest) -> dict:
        fault = None
        for key, kind in self.fault_injection.items():
            if key == "*" or key in req.user:
                fault = kind
                break
        material = _extract(req.user, r"material is exactly:\s*(.+)", "100% cotton")
        color = _extract(req.user, r"colour is exactly:\s*(.+)", "indigo")
        title = f"{color.title()} denim, built to last"
        body = f"Cut for movement in {color} {material}. Raw selvedge. Wear it hard."
        if fault == "banned_phrase" and "FAILED QA" not in req.user:
            title = "This is a must-have game-changer"
            body = "You will be obsessed. Literally the best."
        script = (
            f"This is {color} denim. The fibre is {material}. "
            "Built to last. Cut for movement. Raw selvedge that holds its shape. "
            "Wear it hard through the week. No hype, just a pair that works."
        )
        lo, hi = 0, 0
        m = re.search(r"hashtags: exactly (\d+)-(\d+)", req.user)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
        tags = ["#denim", "#selvedge", "#everyday", "#rawselvedge", "#indigo"][:hi] if hi else []
        if lo and len(tags) < lo:
            tags = (tags + ["#denim", "#selvedge", "#fit"] * lo)[:lo]
        return {
            "title": title[:70],
            "body": body,
            "bullets": ["raw selvedge", "cut for movement"],
            "hashtags": tags,
            "cta": "Shop the pair",
            "alt_text": f"Studio photo of {color} denim garment in {material}",
            "script": script,
            "seo": {"meta_title": title, "meta_description": body[:155], "keywords": ["denim"]},
        }


def _extract(text: str, pat: str, default: str) -> str:
    m = re.search(pat, text, re.I)
    return m.group(1).split("\n")[0].strip() if m else default
