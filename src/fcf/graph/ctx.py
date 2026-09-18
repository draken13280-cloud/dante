from __future__ import annotations

from dataclasses import dataclass, field

from fcf.core.config import settings
from fcf.core.money import Budget
from fcf.domain.brand import BrandKit
from fcf.storage.local import LocalStore


@dataclass
class Ctx:
    job_id: str
    budget: Budget
    store: LocalStore
    prefix: str
    brand: BrandKit | None = None
    assets: dict = field(default_factory=dict)
    timeout_s: int = 120
    force_llm_judge: bool = False
    use_vision: bool = False
    events: list = field(default_factory=list)
    repo: object | None = None
    run_id: str = "run_1"

    async def emit(self, type_: str, **payload) -> None:
        self.events.append({"type": type_, "payload": payload, "job_id": self.job_id})
        if self.repo:
            await self.repo.emit(self.job_id, type_, **payload)

    async def persist_assets(self, job_id: str, assets: dict) -> None:
        pass

    async def persist_qa(self, job_id: str, verdict) -> None:
        pass

    async def persist_publish(self, job_id: str, ch, r) -> None:
        pass

    async def mark_superseded(self, job_id: str, keys) -> None:
        pass

    async def new_run(self, job_id: str, trigger: str, keys: list[str]) -> None:
        pass

    @classmethod
    def from_config(cls, config: dict) -> Ctx:
        conf = (config or {}).get("configurable") or {}
        job_id = conf.get("job_id") or "job"
        if "ctx" in conf:
            return conf["ctx"]
        return cls(
            job_id=job_id,
            budget=Budget(conf.get("budget_limit", settings.default_budget_cents)),
            store=LocalStore(),
            prefix=f"jobs/{job_id}",
            timeout_s=settings.node_timeout_s,
        )
