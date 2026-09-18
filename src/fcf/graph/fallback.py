"""Linear runner of the same node functions for unit tests without LangGraph checkpointing."""

from fcf.graph.nodes import (
    dispatch_regen,
    finalize,
    gen_audio,
    gen_text,
    gen_video,
    gen_visual,
    load_context,
    post_production,
    prompt_matrix,
    publish,
    qa,
    wait_approval,
)
from fcf.graph.nodes import _all_blocked, _has_fatal


async def run_linear(state: dict, config: dict) -> dict:
    for fn in (
        load_context,
        prompt_matrix,
        gen_text,
        gen_visual,
        gen_audio,
        gen_video,
        post_production,
    ):
        upd = await fn(state, config)
        _merge(state, upd)

    loops = 0
    while loops <= 8:
        upd = await qa(state, config)
        _merge(state, upd)
        if state.get("errors") and _has_fatal(state["errors"]):
            break
        if state.get("regen_queue"):
            upd = await dispatch_regen(state, config)
            _merge(state, upd)
            for fn in (gen_text, gen_visual, gen_audio, gen_video, post_production):
                upd = await fn(state, config)
                _merge(state, upd)
            loops += 1
            continue
        break

    if not _all_blocked(state) and not (_has_fatal(state.get("errors"))):
        if state.get("approval") == "pending":
            upd = await wait_approval(state, config)
            _merge(state, upd)
        if state.get("approval") in ("approved", "not_required"):
            upd = await publish(state, config)
            _merge(state, upd)
    upd = await finalize(state, config)
    _merge(state, upd)
    return state


def _merge(state: dict, upd: dict | None) -> None:
    if not upd:
        return
    for k, v in upd.items():
        if k in ("assets", "qa", "feedback", "regen_count") and isinstance(v, dict):
            state.setdefault(k, {})
            state[k].update(v)
        elif k in ("errors", "publish_results") and isinstance(v, list):
            state.setdefault(k, [])
            state[k].extend(v)
        elif k == "spent_cents":
            state[k] = state.get("spent_cents", 0) + (v or 0)
        else:
            state[k] = v
