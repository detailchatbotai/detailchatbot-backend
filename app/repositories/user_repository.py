from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.user import User

class UserRepository:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        user = await db.execute(select(User).where(User.email == email))
        return user.scalar_one_or_none()

    @staticmethod
    async def get_by_supabase_user_id(db: AsyncSession, supabase_user_id: str) -> Optional[User]:
        user = await db.execute(select(User).where(User.supabase_user_id == supabase_user_id))
        return user.scalar_one_or_none()

    @staticmethod
    async def get_by_subscription_id(db: AsyncSession, subscription_id: str) -> Optional[User]:
        user = await db.execute(select(User).where(User.stripe_subscription_id == subscription_id))
        return user.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        *,
        email: str,
        hashed_password: str,
        shop_name: str,
        plan: str,
        is_subscribed: bool,
        is_active: bool,
        supabase_user_id: str
    ) -> User | None:
        """
        Create a user in the local users table after successful Supabase Auth signup.
        Returns the user if successful, or None if a unique constraint is violated.
        """
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            shop_name=shop_name,
            plan=plan,
            is_subscribed=is_subscribed,
            is_active=is_active,
            supabase_user_id=supabase_user_id
        )
        db.add(new_user)
        try:
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except Exception as e:
            await db.rollback()
            return None

    @staticmethod
    async def delete_by_supabase_user_id(db: AsyncSession, supabase_user_id: str) -> None:
        """
        Delete a user from the local users table by supabase_user_id.
        """
        user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
        if user:
            await db.delete(user)
            await db.commit()
