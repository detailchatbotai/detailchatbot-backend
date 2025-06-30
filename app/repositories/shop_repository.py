from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.models.shop import Shop

class ShopRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, shop_id: int) -> Optional[Shop]:
        result = await db.execute(select(Shop).where(Shop.id == shop_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Shop]:
        result = await db.execute(select(Shop).where(Shop.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_owner_id(db: AsyncSession, owner_id: int) -> List[Shop]:
        result = await db.execute(select(Shop).where(Shop.owner_id == owner_id))
        return result.scalars().all()

    @staticmethod
    async def create_shop(
        db: AsyncSession,
        *,
        name: str,
        owner_id: int,
        services: str = None,
        pricing: str = None,
        hours: str = None,
        location: str = None,
        description: str = None
    ) -> Shop:
        new_shop = Shop(
            name=name,
            owner_id=owner_id,
            services=services,
            pricing=pricing,
            hours=hours,
            location=location,
            description=description
        )
        db.add(new_shop)
        await db.commit()
        await db.refresh(new_shop)
        return new_shop

    @staticmethod
    async def update_shop(
        db: AsyncSession,
        shop: Shop,
        **kwargs
    ) -> Shop:
        for key, value in kwargs.items():
            setattr(shop, key, value)
        await db.commit()
        await db.refresh(shop)
        return shop

    @staticmethod
    async def delete_shop(db: AsyncSession, shop: Shop) -> None:
        await db.delete(shop)
        await db.commit()

