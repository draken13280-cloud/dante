from fastapi import FastAPI

from fcf.api.routers import analytics, assets, brands, health, jobs, products
from fcf.core.logging import configure_logging
from fcf.providers.register_all import register_defaults

configure_logging()
register_defaults()

app = FastAPI(title="Fashion Content Factory", version="0.2.0")
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(brands.router)
app.include_router(products.router)
app.include_router(assets.router)
app.include_router(analytics.router)
