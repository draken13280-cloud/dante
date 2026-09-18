from fastapi import APIRouter, Depends

from fcf.api.deps import get_repo
from fcf.db.repo import Repo
from fcf.domain.product import Product

router = APIRouter()


@router.post("/products")
async def create_product(body: Product, repo: Repo = Depends(get_repo)):
    row = await repo.create_product(body)
    return {"id": row.id, "sku": row.sku}


@router.get("/products")
async def list_products(brand: str | None = None, q: str | None = None, repo: Repo = Depends(get_repo)):
    ids = await repo.filter_products(brand=brand, q=q)
    return {"ids": ids}
