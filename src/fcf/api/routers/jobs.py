from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from fcf.api.deps import get_repo
from fcf.core.config import settings
from fcf.db.repo import Repo
from fcf.providers.register_all import register_defaults

router = APIRouter()
register_defaults()


class JobCreate(BaseModel):
    product_id: str
    channels: list[str]
    mode: str | None = None
    budget_cents: int | None = None
    approval_required: bool | None = None


class JobOut(BaseModel):
    id: str
    status: str
    product_id: str
    channels: list
    mode: str
    budget_cents: int

    class Config:
        from_attributes = True


class ApprovalIn(BaseModel):
    decision: str
    notes: str | None = None
    user: str | None = None


class RegenIn(BaseModel):
    asset_keys: list[str]
    feedback: dict[str, list[str]] = Field(default_factory=dict)


class BatchCreate(BaseModel):
    product_ids: list[str] | None = None
    filter: dict = Field(default_factory=dict)
    channels: list[str]
    budget_cents: int | None = None
    max_total_cents: int = 10_000
    mode: str | None = None
    approval_required: bool | None = None

    def job_kwargs(self):
        return dict(
            channels=self.channels,
            mode=self.mode or settings.mode.value,
            budget_cents=self.budget_cents or settings.default_budget_cents,
            approval_required=self.approval_required
            if self.approval_required is not None
            else settings.approval_required_default,
        )


@router.post("/jobs", response_model=JobOut, status_code=202)
async def create_job(body: JobCreate, repo: Repo = Depends(get_repo)):
    job = await repo.create_job(
        product_id=body.product_id,
        channels=body.channels,
        mode=body.mode or settings.mode.value,
        budget_cents=body.budget_cents or settings.default_budget_cents,
        approval_required=body.approval_required
        if body.approval_required is not None
        else settings.approval_required_default,
    )
    return job


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: str, repo: Repo = Depends(get_repo)):
    try:
        return await repo.get_job(job_id)
    except KeyError:
        raise HTTPException(404)


@router.get("/jobs/{job_id}/events")
async def stream_events(job_id: str, repo: Repo = Depends(get_repo)):
    async def gen():
        last = 0
        import asyncio

        idle = 0
        while idle < 30:
            rows = await repo.events_after(job_id, last)
            for e in rows:
                last = e.id
                yield f"event: {e.type}\ndata: {json.dumps(e.payload)}\n\n"
                if e.type == "job.finished":
                    return
            if not rows:
                idle += 1
                await asyncio.sleep(1)
            else:
                idle = 0

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/jobs/{job_id}/approve")
async def approve(job_id: str, body: ApprovalIn, repo: Repo = Depends(get_repo)):
    job = await repo.get_job(job_id)
    if job.status != "awaiting_approval":
        raise HTTPException(409, f"job is {job.status}")
    return {"ok": True, "decision": body.decision}


@router.post("/jobs/{job_id}/regenerate")
async def manual_regen(job_id: str, body: RegenIn):
    return {"ok": True, "keys": body.asset_keys}


@router.post("/jobs/batch", status_code=202)
async def create_batch(body: BatchCreate, repo: Repo = Depends(get_repo)):
    ids = body.product_ids or await repo.filter_products(**body.filter)
    total = len(ids) * (body.budget_cents or settings.default_budget_cents)
    if total > body.max_total_cents:
        raise HTTPException(400, f"batch would cost up to {total}c > cap {body.max_total_cents}c")
    jobs = [await repo.create_job(product_id=p, **body.job_kwargs()) for p in ids]
    return {"created": len(jobs), "job_ids": [j.id for j in jobs]}
