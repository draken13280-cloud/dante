from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fcf.core.ids import new_id
from fcf.db import models as m
from fcf.domain.brand import BrandKit
from fcf.domain.product import Product as DomainProduct


class Repo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def upsert_brand(self, kit: BrandKit) -> m.Brand:
        row = await self.s.get(m.Brand, kit.slug)
        if row:
            row.name = kit.name
            row.kit = kit.model_dump(mode="json")
        else:
            row = m.Brand(id=kit.slug, name=kit.name, kit=kit.model_dump(mode="json"))
            self.s.add(row)
        await self.s.flush()
        return row

    async def get_brand(self, slug: str) -> BrandKit:
        row = await self.s.get(m.Brand, slug)
        if not row:
            raise KeyError(slug)
        return BrandKit.model_validate(row.kit)

    async def create_product(self, p: DomainProduct) -> m.Product:
        row = m.Product(
            id=p.id,
            brand_id=p.brand_slug,
            sku=p.sku,
            title=p.title,
            attrs=p.attrs.model_dump(),
            source_images=[str(u) for u in p.source_images],
        )
        self.s.add(row)
        await self.s.flush()
        return row

    async def get_product(self, pid: str) -> DomainProduct:
        row = await self.s.get(m.Product, pid)
        if not row:
            raise KeyError(pid)
        return DomainProduct(
            id=row.id,
            brand_slug=row.brand_id,
            sku=row.sku,
            title=row.title,
            attrs=row.attrs,
            source_images=row.source_images or [],
        )

    async def filter_products(self, brand: str | None = None, q: str | None = None) -> list[str]:
        stmt = select(m.Product.id)
        if brand:
            stmt = stmt.where(m.Product.brand_id == brand)
        if q:
            stmt = stmt.where(m.Product.title.ilike(f"%{q}%"))
        return list((await self.s.execute(stmt)).scalars())

    async def create_job(
        self,
        *,
        product_id: str,
        channels: list[str],
        mode: str,
        budget_cents: int,
        approval_required: bool,
    ) -> m.Job:
        product = await self.s.get(m.Product, product_id)
        job = m.Job(
            id=new_id("job_"),
            product_id=product_id,
            brand_id=product.brand_id,
            status="queued",
            mode=mode,
            channels=channels,
            budget_cents=budget_cents,
            approval_required=approval_required,
            thread_id=new_id("thr_"),
        )
        self.s.add(job)
        await self.s.flush()
        return job

    async def get_job(self, job_id: str) -> m.Job:
        job = await self.s.get(m.Job, job_id)
        if not job:
            raise KeyError(job_id)
        return job

    async def start_job(self, job_id: str) -> m.Job:
        job = await self.get_job(job_id)
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await self.s.flush()
        return job

    async def set_status(self, job_id: str, status: str) -> None:
        job = await self.get_job(job_id)
        job.status = status
        await self.s.flush()

    async def finish_job(self, job_id: str, status: str, spent: int) -> None:
        job = await self.get_job(job_id)
        job.status = status
        job.spent_cents = spent
        job.finished_at = datetime.now(timezone.utc)
        await self.s.flush()

    async def fail_job(self, job_id: str, error: str) -> None:
        job = await self.get_job(job_id)
        job.status = "failed"
        job.error = error
        job.finished_at = datetime.now(timezone.utc)
        await self.s.flush()

    async def emit(self, job_id: str, type_: str, **payload) -> None:
        self.s.add(m.Event(job_id=job_id, type=type_, payload=payload))
        await self.s.flush()

    async def events_after(self, job_id: str, last_id: int) -> list[m.Event]:
        stmt = (
            select(m.Event)
            .where(m.Event.job_id == job_id, m.Event.id > last_id)
            .order_by(m.Event.id)
        )
        return list((await self.s.execute(stmt)).scalars())

    async def persist_asset(self, job_id: str, run_id: str, key: str, data: dict) -> m.Asset:
        parts = key.split(":")
        row = m.Asset(
            id=new_id("ast_"),
            job_id=job_id,
            run_id=run_id,
            key=key,
            kind=parts[0],
            channel=parts[1] if len(parts) > 1 else "",
            variant=parts[2] if len(parts) > 2 else "a",
            locale=parts[3] if len(parts) > 3 else "en",
            uri=data.get("uri", ""),
            content=data.get("content"),
            meta=data.get("meta") or {},
            status="draft",
        )
        self.s.add(row)
        await self.s.flush()
        return row
