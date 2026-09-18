"""Run a mock pipeline for a sample SKU without Postgres."""

from __future__ import annotations

import argparse
import asyncio
import yaml
from pathlib import Path

from fcf.core.ids import new_id
from fcf.core.money import Budget
from fcf.domain.brand import BrandKit
from fcf.domain.product import Product, ProductAttrs
from fcf.graph.ctx import Ctx
from fcf.graph.fallback import run_linear
from fcf.providers.register_all import register_defaults
from fcf.storage.local import LocalStore


async def main(sku: str) -> None:
    register_defaults()
    kit_path = Path("brandkits/acme_denim.yaml")
    brand = BrandKit.model_validate(yaml.safe_load(kit_path.read_text()))
    product = Product(
        id="prod_demo",
        brand_slug=brand.slug,
        sku=sku,
        title="ACME Selvedge Straight",
        attrs=ProductAttrs(
            color="indigo",
            color_hex="#1B2A41",
            material="100% cotton",
            material_tokens=["cotton", "denim"],
        ),
    )
    job_id = new_id("job_")
    ctx = Ctx(job_id=job_id, budget=Budget(250), store=LocalStore(), prefix=f"jobs/{job_id}")
    state = {
        "job_id": job_id,
        "thread_id": "thr_demo",
        "mode": "mock",
        "run_version": 1,
        "product": product.model_dump(),
        "brand": brand.model_dump(),
        "channels": ["tiktok", "shopify"],
        "budget_limit": 250,
        "spent_cents": 0,
        "assets": {},
        "qa": {},
        "feedback": {},
        "regen_count": {},
        "total_regens": 0,
        "approval": "not_required",
        "publish_results": [],
        "errors": [],
        "status": "running",
    }
    await run_linear(state, {"configurable": {"ctx": ctx, "job_id": job_id}})
    print("status", state["status"], "assets", list(state["assets"]))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--sku", default="ACME-DNM-001")
    args = p.parse_args()
    asyncio.run(main(args.sku))
