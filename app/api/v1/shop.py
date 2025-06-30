from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.repositories.shop_repository import ShopRepository
from app.repositories.user_repository import UserRepository
from app.schemas.shop import ShopCreate, ShopUpdate, ShopRead
from app.services.auth_service import AuthService
from app.services.shop_service import ShopService

router = APIRouter(prefix="/shop", tags=["shop"])

@router.post("/", response_model=ShopRead, status_code=status.HTTP_201_CREATED)
async def create_shop(
    data: ShopCreate,
    db: AsyncSession = Depends(get_db),
    supabase_user_id: str = Depends(AuthService.get_current_user_supabase_id)
):
    """
    Create a shop for an authenticated user.
    """
    return await ShopService.create_shop(db, supabase_user_id, data)

@router.get("/owner/me", response_model=List[ShopRead])
async def get_my_shops(
    db: AsyncSession = Depends(get_db),
    supabase_user_id: str = Depends(AuthService.get_current_user_supabase_id)
):
    user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    shops = await ShopRepository.get_by_owner_id(db, user.id)
    return shops

@router.get("/{shop_id}", response_model=ShopRead)
async def get_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    shop = await ShopRepository.get_by_id(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop

@router.put("/{shop_id}", response_model=ShopRead)
async def update_shop(
    shop_id: int,
    data: ShopUpdate,
    db: AsyncSession = Depends(get_db),
    supabase_user_id: str = Depends(AuthService.get_current_user_supabase_id)
):
    shop = await ShopRepository.get_by_id(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
    if not user or shop.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this shop")
    updated_shop = await ShopRepository.update_shop(db, shop, **data.dict(exclude_unset=True))
    return updated_shop

@router.delete("/{shop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shop(
    shop_id: int,
    db: AsyncSession = Depends(get_db),
    supabase_user_id: str = Depends(AuthService.get_current_user_supabase_id)
):
    shop = await ShopRepository.get_by_id(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
    if not user or shop.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this shop")
    await ShopRepository.delete_shop(db, shop)
    return None
