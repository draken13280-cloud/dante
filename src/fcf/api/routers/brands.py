from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from fcf.api.deps import get_repo
from fcf.db.repo import Repo
from fcf.domain.brand import BrandKit

router = APIRouter()


class BrandIn(BaseModel):
    kit: dict


@router.post("/brands")
async def create_brand(body: BrandIn, repo: Repo = Depends(get_repo)):
    kit = BrandKit.model_validate(body.kit)
    row = await repo.upsert_brand(kit)
    return {"id": row.id, "name": row.name}


@router.put("/brands/{slug}")
async def put_brand(slug: str, body: BrandIn, repo: Repo = Depends(get_repo)):
    kit = BrandKit.model_validate({**body.kit, "slug": slug})
    row = await repo.upsert_brand(kit)
    return {"id": row.id}


@router.get("/brands/{slug}")
async def get_brand(slug: str, repo: Repo = Depends(get_repo)):
    try:
        kit = await repo.get_brand(slug)
    except KeyError:
        raise HTTPException(404)
    return kit.model_dump()
