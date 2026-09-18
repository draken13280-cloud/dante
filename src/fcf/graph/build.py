try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # optional extra
    END = START = StateGraph = None  # type: ignore

from fcf.graph.nodes import (
    dispatch_regen,
    finalize,
    gen_audio,
    gen_text,
    gen_video,
    gen_visual,
    join_media,
    load_context,
    post_production,
    prompt_matrix,
    publish,
    qa,
    wait_approval,
)
from fcf.graph.nodes import _all_blocked, _has_fatal
from fcf.graph.state import PipelineState


def route_after_qa(state) -> str:
    if state.get("errors") and _has_fatal(state["errors"]):
        return "finalize"
    if state.get("regen_queue"):
        return "dispatch_regen"
    if _all_blocked(state):
        return "finalize"
    if state.get("approval") == "pending":
        return "wait_approval"
    return "publish"


def route_after_approval(state) -> str:
    return "publish" if state.get("approval") == "approved" else "finalize"


def build_graph(checkpointer=None):
    g = StateGraph(PipelineState)
    for name, fn in [
        ("load_context", load_context),
        ("prompt_matrix", prompt_matrix),
        ("gen_text", gen_text),
        ("gen_visual", gen_visual),
        ("gen_audio", gen_audio),
        ("join_media", join_media),
        ("gen_video", gen_video),
        ("post_production", post_production),
        ("qa", qa),
        ("dispatch_regen", dispatch_regen),
        ("wait_approval", wait_approval),
        ("publish", publish),
        ("finalize", finalize),
    ]:
        g.add_node(name, fn)
    g.add_edge(START, "load_context")
    g.add_edge("load_context", "prompt_matrix")
    g.add_edge("prompt_matrix", "gen_text")
    g.add_edge("gen_text", "gen_visual")
    g.add_edge("gen_text", "gen_audio")
    g.add_edge("gen_visual", "join_media")
    g.add_edge("gen_audio", "join_media")
    g.add_edge("join_media", "gen_video")
    g.add_edge("gen_video", "post_production")
    g.add_edge("post_production", "qa")
    g.add_conditional_edges(
        "qa", route_after_qa, ["dispatch_regen", "wait_approval", "publish", "finalize"]
    )
    g.add_edge("dispatch_regen", "gen_text")
    g.add_conditional_edges("wait_approval", route_after_approval, ["publish", "finalize"])
    g.add_edge("publish", "finalize")
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)


async def get_app():
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    from fcf.core.config import settings

    saver = AsyncPostgresSaver.from_conn_string(settings.database_url.replace("+asyncpg", ""))
    await saver.setup()
    return build_graph(saver)
