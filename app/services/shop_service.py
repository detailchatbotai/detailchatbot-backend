from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.repositories.shop_repository import ShopRepository
from app.schemas.shop import ShopCreate

class ShopService:
    @staticmethod
    async def create_shop(db: AsyncSession, supabase_user_id: str, data: ShopCreate):
        user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        existing = await ShopRepository.get_by_name(db, data.name)
        if existing:
            raise HTTPException(status_code=400, detail="Shop name already exists")
        shop = await ShopRepository.create_shop(
            db,
            name=data.name,
            owner_id=user.id,
            services=data.services,
            pricing=data.pricing,
            hours=data.hours,
            location=data.location,
            description=data.description
        )
        return shop

