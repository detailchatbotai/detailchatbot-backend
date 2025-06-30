from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from datetime import datetime

class ChatbotRepository:
    @staticmethod
    async def get_usage(db: AsyncSession, supabase_user_id: str) -> tuple[int, datetime | None]:
        user = await db.execute(select(User).where(User.supabase_user_id == supabase_user_id))
        user = user.scalar_one_or_none()
        if user:
            return getattr(user, "ai_query_usage", 0), getattr(user, "ai_usage_reset", None)
        return 0, None

    @staticmethod
    async def increment_usage(db: AsyncSession, supabase_user_id: str) -> None:
        user = await db.execute(select(User).where(User.supabase_user_id == supabase_user_id))
        user = user.scalar_one_or_none()
        if user:
            user.ai_query_usage = getattr(user, "ai_query_usage", 0) + 1
            await db.commit()
            await db.refresh(user)

    @staticmethod
    async def reset_usage(db: AsyncSession, supabase_user_id: str) -> None:
        user = await db.execute(select(User).where(User.supabase_user_id == supabase_user_id))
        user = user.scalar_one_or_none()
        if user:
            user.ai_query_usage = 0
            user.ai_usage_reset = datetime.utcnow()
            await db.commit()
            await db.refresh(user)

