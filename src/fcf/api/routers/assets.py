from fastapi import APIRouter

router = APIRouter()


@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    return {"id": asset_id}


@router.get("/assets/{asset_id}/qa")
async def get_asset_qa(asset_id: str):
    return {"id": asset_id, "qa": []}
