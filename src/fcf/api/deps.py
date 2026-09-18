from collections.abc import AsyncIterator

from fcf.db.base import SessionLocal
from fcf.db.repo import Repo


async def get_repo() -> AsyncIterator[Repo]:
    async with SessionLocal() as s:
        repo = Repo(s)
        yield repo
        await s.commit()
