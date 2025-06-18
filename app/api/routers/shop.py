from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.services.shop import get_shop
from app.core.database import get_db
from app.schemas.shop import ShopRead

router = APIRouter(tags=["shop"])

@router.get("/shop/{shop_id}", response_model=ShopRead)
async def read_shop(
    shop_id: str,
    db: AsyncSession = Depends(get_db)      # ← use the get_db() from core.database
):
    return await get_shop(db, shop_id)
