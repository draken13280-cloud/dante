from typing import Annotated, Literal, TypedDict
import operator


def merge_dict(a: dict, b: dict) -> dict:
    return {**(a or {}), **(b or {})}


class PipelineState(TypedDict, total=False):
    job_id: str
    thread_id: str
    mode: str
    run_version: int
    product: dict
    brand: dict
    channels: list[str]
    plan: dict | None
    stage_filter: list[str] | None
    assets: Annotated[dict[str, dict], merge_dict]
    qa: Annotated[dict[str, dict], merge_dict]
    feedback: Annotated[dict[str, list[str]], merge_dict]
    regen_queue: list[str]
    regen_count: Annotated[dict[str, int], merge_dict]
    total_regens: int
    budget_limit: int
    spent_cents: Annotated[int, operator.add]
    approval: Literal["not_required", "pending", "approved", "rejected"]
    publish_results: Annotated[list[dict], operator.add]
    errors: Annotated[list[dict], operator.add]
    status: str
