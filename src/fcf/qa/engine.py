from __future__ import annotations

from dataclasses import asdict, dataclass, field

from fcf.domain.assets import AssetRef
from fcf.domain.brand import BrandKit
from fcf.domain.enums import AssetKind, Severity
from fcf.domain.plan import AssetSpec
from fcf.domain.product import Product


@dataclass(slots=True)
class QACheck:
    rule: str
    passed: bool
    severity: Severity
    score: float
    detail: str
    fix_hint: str | None = None


@dataclass(slots=True)
class QAVerdict:
    key: str
    verdict: str
    checks: list[QACheck] = field(default_factory=list)
    cost_cents: int = 0

    @property
    def fix_hints(self) -> list[str]:
        return [c.fix_hint for c in self.checks if not c.passed and c.fix_hint]

    @classmethod
    def aggregate(cls, key, checks, cost=0):
        failed = [c for c in checks if not c.passed]
        if any(c.severity is Severity.BLOCKER for c in failed):
            v = "fail"
        elif any(c.severity is Severity.MAJOR for c in failed):
            v = "fail"
        elif failed:
            v = "warn"
        else:
            v = "pass"
        return cls(key=key, verdict=v, checks=checks, cost_cents=cost)

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "verdict": self.verdict,
            "checks": [asdict(c) | {"severity": c.severity.value} for c in self.checks],
            "cost_cents": self.cost_cents,
            "fix_hints": self.fix_hints,
        }


class QAEngine:
    def __init__(self, brand: BrandKit, product: Product, ctx, *, use_llm=True, use_vision=False):
        self.brand = brand
        self.product = product
        self.ctx = ctx
        self.use_llm = use_llm
        self.use_vision = use_vision

    async def review(self, spec: AssetSpec, asset: AssetRef) -> QAVerdict:
        from fcf.qa.judge_llm import judge_copy
        from fcf.qa.judge_vision import judge_visual
        from fcf.qa.rules_media import check_audio, check_image, check_video
        from fcf.qa.rules_text import check_copy

        pol = self.brand.channels[spec.channel]
        checks: list[QACheck] = []
        if spec.kind is AssetKind.COPY:
            checks += check_copy(asset.content or {}, self.product, self.brand, pol)
        elif spec.kind is AssetKind.IMAGE:
            path = asset.local_path or (asset.uri.removeprefix("file://") if asset.uri.startswith("file://") else None)
            checks += check_image(asset.meta, path, self.product, self.brand, pol)
        elif spec.kind is AssetKind.AUDIO:
            checks += check_audio(asset.meta, pol)
        elif spec.kind is AssetKind.VIDEO:
            checks += check_video(asset.meta, asset.meta.get("srt"), pol)

        blocking_failed = any(not c.passed and c.severity is Severity.BLOCKER for c in checks)
        if not blocking_failed and self.use_llm and spec.kind is AssetKind.COPY:
            checks += await judge_copy(asset.content, self.product, self.brand, self.ctx)
        if not blocking_failed and self.use_vision and spec.kind in (AssetKind.IMAGE, AssetKind.VIDEO):
            checks += await judge_visual(asset, self.product, self.brand, self.ctx)
        return QAVerdict.aggregate(spec.key, checks, 0)
