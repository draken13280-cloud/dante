from fcf.core.config import settings
from fcf.providers.register_all import register_defaults


async def startup(ctx):
    register_defaults()
    ctx["graph"] = None
    ctx["repo"] = None


async def run_pipeline(bctx, job_id: str):
    return job_id


async def resume_pipeline(bctx, job_id: str, decision: dict):
    return job_id


async def regen_pipeline(bctx, job_id: str, keys: list[str], feedback: dict):
    return job_id


async def collect_metrics(bctx):
    return None


try:
    from arq import cron
    from arq.connections import RedisSettings

    class WorkerSettings:
        functions = [run_pipeline, resume_pipeline, regen_pipeline]
        cron_jobs = [cron(collect_metrics, hour=3)]
        redis_settings = RedisSettings.from_dsn(settings.redis_url)
        max_jobs = 4
        job_timeout = 1800
        on_startup = startup
except ImportError:
    WorkerSettings = None  # type: ignore
