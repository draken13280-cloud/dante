from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fcf.core.config import settings
from fcf.db.models import Base

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
