from __future__ import annotations

import asyncio
import random

from fcf.core.errors import BudgetExceeded, TransientProviderError
from fcf.providers.base import get


async def call_provider(kind, method, req, *, ctx, provider_name=None, attempts=3):
    prov = get(kind, provider_name)
    est = prov.estimate_cost(req)
    ctx.budget.reserve(est)

    delay = 1.0
    for i in range(attempts):
        try:
            res = await asyncio.wait_for(getattr(prov, method)(req), timeout=ctx.timeout_s)
            actual = getattr(getattr(res, "usage", None), "cost_cents", 0) or 0
            ctx.budget.commit(actual, reserved=est)
            await ctx.emit(
                "provider.call",
                provider=prov.name,
                kind=kind,
                ok=True,
                cost_cents=actual,
                latency_ms=getattr(res.usage, "latency_ms", 0),
            )
            return res
        except TransientProviderError as e:
            if i == attempts - 1:
                ctx.budget.release(est)
                raise
            await ctx.emit("provider.retry", provider=prov.name, attempt=i + 1, error=str(e))
            await asyncio.sleep(delay + random.uniform(0, 0.4))
            delay *= 2
        except Exception:
            ctx.budget.release(est)
            await ctx.emit("provider.call", provider=prov.name, kind=kind, ok=False)
            raise
