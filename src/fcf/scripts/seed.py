from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import yaml

from fcf.db.base import SessionLocal, init_db
from fcf.db.repo import Repo
from fcf.domain.brand import BrandKit


async def main(path: str) -> None:
    await init_db()
    data = yaml.safe_load(Path(path).read_text())
    kit = BrandKit.model_validate(data)
    async with SessionLocal() as s:
        repo = Repo(s)
        await repo.upsert_brand(kit)
        await s.commit()
    print(f"seeded brand {kit.slug}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
