import pytest

from fcf.core.ids import asset_key
from fcf.core.money import Budget
from fcf.domain.enums import AssetKind, Channel
from fcf.graph.ctx import Ctx
from fcf.graph.fallback import run_linear
from fcf.graph.nodes import downstream_closure
from fcf.agents.prompt_matrix import deterministic_plan
from fcf.providers.mock.llm import MockLLM
from fcf.storage.local import LocalStore


def _state(product, brand, channels, approval="not_required"):
    return {
        "job_id": "job_test",
        "thread_id": "thr",
        "mode": "mock",
        "run_version": 1,
        "product": product.model_dump(),
        "brand": brand.model_dump(),
        "channels": channels,
        "budget_limit": 250,
        "spent_cents": 0,
        "assets": {},
        "qa": {},
        "feedback": {},
        "regen_count": {},
        "total_regens": 0,
        "approval": approval,
        "publish_results": [],
        "errors": [],
        "status": "running",
    }


@pytest.mark.asyncio
async def test_failed_copy_regenerates_only_its_branch(product, brand):
    MockLLM.fault_injection = {"copy:tiktok:a:en": "banned_phrase"}
    ctx = Ctx(job_id="job_test", budget=Budget(250), store=LocalStore("/tmp/fcf-t"), prefix="t")
    state = _state(product, brand, ["tiktok", "shopify"])
    await run_linear(state, {"configurable": {"ctx": ctx, "job_id": "job_test"}})
    regen = [e for e in ctx.events if e["type"] == "regen.enqueued"]
    assert regen, "expected at least one regen"
    keys = set()
    for e in regen:
        keys.update(e["payload"]["keys"])
    assert "copy:tiktok:a:en" in keys
    assert "audio:tiktok:a:en" in keys
    assert "video:tiktok:a:en" in keys
    assert not any(k.startswith("copy:shopify") for k in keys)
    assert state["status"] in ("done", "failed")


def test_downstream_closure(product, brand):
    plan = deterministic_plan(product, brand, [Channel.TIKTOK, Channel.SHOPIFY])
    keys = downstream_closure(plan, {"copy:tiktok:a:en"})
    assert "copy:tiktok:a:en" in keys
    assert "audio:tiktok:a:en" in keys
    assert "video:tiktok:a:en" in keys
    assert not any(k.startswith("copy:shopify") for k in keys)


@pytest.mark.asyncio
async def test_youtube_is_explicitly_unsupported(product, brand):
    from fcf.publish.dispatcher import dispatch_publish

    ctx = Ctx(job_id="job_yt", budget=Budget(250), store=LocalStore("/tmp/fcf-t"), prefix="t")
    state = _state(product, brand, ["tiktok"])
    state["extra_platforms"] = ["youtube_shorts"]
    results = await dispatch_publish(state, ctx)
    by_plat = {r.get("platform"): r.get("status") for r in results}
    assert by_plat.get("youtube_shorts") == "unsupported"


@pytest.mark.asyncio
async def test_budget_stops_before_spending(product, brand):
    from fcf.core.errors import BudgetExceeded
    from fcf.core.money import Budget as B

    b = B(1, 0)
    with pytest.raises(BudgetExceeded):
        b.reserve(4)
    assert b.spent == 0
