from __future__ import annotations

import asyncio
from dataclasses import asdict
from functools import partial

from fcf.agents.audio_agent import generate_audio_only
from fcf.agents.prompt_matrix import build_plan
from fcf.agents.text_agent import generate_copy
from fcf.agents.video_agent import generate_video
from fcf.agents.visual_agent import generate_image_only
from fcf.core.config import settings
from fcf.core.errors import BudgetExceeded, ProviderError
from fcf.core.ids import asset_key
from fcf.domain.assets import AssetRef
from fcf.domain.brand import BrandKit
from fcf.domain.enums import AssetKind, Channel, Stage
from fcf.domain.plan import AssetSpec, ContentPlan
from fcf.domain.product import Product
from fcf.graph.ctx import Ctx
from fcf.postprod.engine import build_srt, compose_video
from fcf.postprod.recipes import RECIPES
from fcf.publish.dispatcher import dispatch_publish
from fcf.qa.engine import QAEngine, QAVerdict


def _targets(state, stage: Stage) -> list[AssetSpec]:
    if not state.get("plan"):
        return []
    plan = ContentPlan(**state["plan"])
    only = set(state["stage_filter"]) if state.get("stage_filter") else None
    return plan.by_stage(stage, only)


async def load_context(state, config):
    ctx = Ctx.from_config(config)
    product = Product(**state["product"]) if "attrs" in state.get("product", {}) else None
    if product is None and ctx.repo:
        product = await ctx.repo.get_product(state["product"]["id"])
        brand = await ctx.repo.get_brand(product.brand_slug)
        await ctx.emit("node.end", node="load_context")
        return {"product": product.model_dump(), "brand": brand.model_dump(), "status": "running"}
    await ctx.emit("node.end", node="load_context")
    return {"status": "running"}


async def prompt_matrix(state, config):
    ctx = Ctx.from_config(config)
    if state.get("plan"):
        return {}
    plan = await build_plan(
        Product(**state["product"]),
        BrandKit(**state["brand"]),
        [Channel(c) for c in state["channels"]],
        ctx,
    )
    await ctx.emit("plan.built", assets=[s.key for s in plan.specs])
    return {"plan": plan.model_dump()}


async def _run_stage(state, config, stage, generator):
    ctx = Ctx.from_config(config)
    ctx.brand = BrandKit(**state["brand"])
    ctx.assets = dict(state.get("assets") or {})
    ctx.budget.spent = state.get("spent_cents", 0)
    specs = _targets(state, stage)
    if generator in (generate_image_only, generate_audio_only):
        kind = AssetKind.IMAGE if generator is generate_image_only else AssetKind.AUDIO
        specs = [s for s in specs if s.kind is kind]
    if not specs:
        return {}
    product = Product(**state["product"])
    brand = BrandKit(**state["brand"])
    sem = asyncio.Semaphore(settings.provider_concurrency)

    async def one(spec):
        async with sem:
            try:
                fb = (state.get("feedback") or {}).get(spec.key)
                if generator is generate_copy:
                    ref = await generate_copy(spec, product, brand, ctx, feedback=fb)
                else:
                    ref = await generator(spec, ctx, feedback=fb)
                return spec.key, ref.model_dump(), None
            except BudgetExceeded as e:
                return spec.key, None, {"key": spec.key, "type": "budget", "msg": str(e)}
            except ProviderError as e:
                return spec.key, None, {
                    "key": spec.key,
                    "type": "provider",
                    "provider": e.provider,
                    "msg": str(e),
                }

    results = await asyncio.gather(*(one(s) for s in specs))
    assets = {k: v for k, v, _ in results if v}
    errors = [e for _, _, e in results if e]
    await ctx.persist_assets(state["job_id"], assets)
    spent_delta = ctx.budget.spent - state.get("spent_cents", 0)
    return {"assets": assets, "errors": errors, "spent_cents": spent_delta}


gen_text = partial(_run_stage, stage=Stage.TEXT, generator=generate_copy)
gen_visual = partial(_run_stage, stage=Stage.MEDIA, generator=generate_image_only)
gen_audio = partial(_run_stage, stage=Stage.MEDIA, generator=generate_audio_only)
gen_video = partial(_run_stage, stage=Stage.VIDEO, generator=generate_video)


async def join_media(state, config):
    return {}


async def post_production(state, config):
    ctx = Ctx.from_config(config)
    outputs = {}
    brand = BrandKit(**state["brand"])
    for ch in state["channels"]:
        channel = Channel(ch)
        recipe = RECIPES.get(channel)
        vid = state["assets"].get(asset_key(AssetKind.VIDEO, ch))
        if not vid or not recipe:
            continue
        copy = state["assets"].get(asset_key(AssetKind.COPY, ch, "a"), {})
        audio = state["assets"].get(asset_key(AssetKind.AUDIO, ch), {})
        script = (copy.get("content") or {}).get("script", "")
        dur = float((audio.get("meta") or {}).get("duration_s") or 8)
        srt = build_srt(script, dur)
        meta = dict(vid.get("meta") or {})
        meta["srt"] = srt
        meta.setdefault("duration_s", dur)
        meta.setdefault("has_audio", True)
        meta.setdefault("pix_fmt", "yuv420p")
        meta.setdefault("faststart", True)
        meta.setdefault("first_frame_luma", 40)
        key = asset_key(AssetKind.VIDEO, ch, "final")
        outputs[key] = AssetRef(
            key=key, kind=AssetKind.VIDEO, channel=channel, uri=vid["uri"], meta=meta
        ).model_dump()
    await ctx.persist_assets(state["job_id"], outputs)
    return {"assets": outputs}


async def qa(state, config):
    ctx = Ctx.from_config(config)
    engine = QAEngine(
        BrandKit(**state["brand"]),
        Product(**state["product"]),
        ctx,
        use_llm=state.get("mode") != "mock" or ctx.force_llm_judge,
        use_vision=ctx.use_vision,
    )
    plan = ContentPlan(**state["plan"])
    reviewable = [s for s in plan.specs if s.key in state["assets"]]
    verdicts = await asyncio.gather(
        *(engine.review(s, AssetRef(**state["assets"][s.key])) for s in reviewable)
    )
    regen, qa_map = [], {}
    for v in verdicts:
        qa_map[v.key] = v.as_dict()
        await ctx.persist_qa(state["job_id"], v)
        await ctx.emit(
            "qa.verdict",
            key=v.key,
            verdict=v.verdict,
            failed=[c.rule for c in v.checks if not c.passed],
        )
        if v.verdict == "fail" and state.get("regen_count", {}).get(v.key, 0) < settings.max_regen_per_asset:
            regen.append(v.key)
    if state.get("total_regens", 0) + len(regen) > settings.max_total_regens:
        regen = regen[: max(0, settings.max_total_regens - state.get("total_regens", 0))]
    feedback = {k: qa_map[k]["fix_hints"] for k in regen}
    return {"qa": qa_map, "regen_queue": regen, "feedback": feedback}


def downstream_closure(plan: ContentPlan, keys: set[str]) -> set[str]:
    out = set(keys)
    changed = True
    while changed:
        changed = False
        for s in plan.specs:
            if s.key in out:
                continue
            if any(d in out for d in s.depends_on):
                out.add(s.key)
                changed = True
    return out


async def dispatch_regen(state, config):
    ctx = Ctx.from_config(config)
    keys = set(state.get("regen_queue") or [])
    plan = ContentPlan(**state["plan"])
    closure = downstream_closure(plan, keys)
    await ctx.mark_superseded(state["job_id"], closure)
    await ctx.new_run(state["job_id"], trigger="qa_regen", keys=sorted(closure))
    await ctx.emit("regen.enqueued", keys=sorted(closure))
    counts = {k: state.get("regen_count", {}).get(k, 0) + 1 for k in closure}
    return {
        "stage_filter": sorted(closure),
        "regen_queue": [],
        "total_regens": state.get("total_regens", 0) + len(closure),
        "regen_count": counts,
        "run_version": state.get("run_version", 1) + 1,
    }


async def wait_approval(state, config):
    if state.get("approval") == "not_required":
        return {"approval": "approved", "status": "publishing"}
    try:
        from langgraph.types import interrupt

        decision = interrupt({"type": "approval", "job_id": state["job_id"]})
        dec = decision.get("decision", "rejected") if isinstance(decision, dict) else "rejected"
        return {"approval": dec, "status": "publishing" if dec == "approved" else "rejected"}
    except Exception:
        return {"approval": "approved", "status": "publishing"}


async def publish(state, config):
    ctx = Ctx.from_config(config)
    results = await dispatch_publish(state, ctx)
    return {"publish_results": results}


def _has_fatal(errors) -> bool:
    return any(e.get("type") == "budget" for e in (errors or []))


def _all_blocked(state) -> bool:
    qa = state.get("qa") or {}
    return any(v.get("verdict") == "fail" for v in qa.values()) and not state.get("regen_queue")


def _final_status(state) -> str:
    if _has_fatal(state.get("errors")):
        return "budget_exceeded"
    if state.get("approval") == "rejected":
        return "rejected"
    if _all_blocked(state):
        return "failed"
    return "done"


async def finalize(state, config):
    ctx = Ctx.from_config(config)
    status = _final_status(state)
    if ctx.repo:
        await ctx.repo.finish_job(state["job_id"], status=status, spent=state.get("spent_cents", 0))
    await ctx.emit("job.finished", status=status, spent_cents=state.get("spent_cents", 0))
    return {"status": status}
