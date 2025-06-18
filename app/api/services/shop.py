from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.shop import Shop as ShopModel
from app.schemas.shop import ShopRead

async def get_shop(db: AsyncSession, shop_id: str) -> ShopRead:
    result = await db.execute(select(ShopModel).where(ShopModel.id == shop_id))
    shop = result.scalars().first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return ShopRead.from_orm(shop)
