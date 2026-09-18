from fastapi import APIRouter

from fcf.analytics.queries import summary_sql

router = APIRouter()


@router.get("/analytics/summary")
async def summary(brand: str | None = None, since: str | None = None):
    return {"queries": list(summary_sql.keys()), "brand": brand, "since": since}


@router.post("/webhooks/metrics/{platform}")
async def inbound_metrics(platform: str, body: dict):
    return {"ok": True, "platform": platform}


@router.get("/metrics")
async def prometheus():
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    from fastapi import Response

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
