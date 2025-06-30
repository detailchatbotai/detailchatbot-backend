import openai
from datetime import datetime, timedelta
from app.repositories.chatbot_repository import ChatbotRepository
from app.repositories.user_repository import UserRepository
from app.core.config import settings
from app.schemas.chatbot import ChatResponse, UsageResponse

STARTER_LIMIT = 500

class ChatbotService:
    @staticmethod
    async def ask(db, supabase_user_id: str, question: str) -> ChatResponse:
        user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
        if not user:
            return ChatResponse(answer="User not found.", reached_limit=True)
        # Reset usage if a new month has started
        now = datetime.utcnow()
        if not user.ai_usage_reset or user.ai_usage_reset.month != now.month or user.ai_usage_reset.year != now.year:
            user.ai_query_usage = 0
            user.ai_usage_reset = now
            await db.commit()
            await db.refresh(user)
        # Enforce plan and usage limits
        plan = user.plan or "starter"
        limit = STARTER_LIMIT if plan == "starter" else 2000 if plan == "pro" else float('inf')
        if user.ai_query_usage >= limit:
            return ChatResponse(answer="You have reached your monthly AI query limit for your plan.", usage=user.ai_query_usage, limit=limit, plan=plan, reached_limit=True)
        # Call OpenAI (basic Q&A only for starter)
        # For MVP, use a simple prompt; advanced features can be gated by plan
        openai.api_key = settings.OPENAI_API_KEY
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": question}],
                max_tokens=256,
                temperature=0.7
            )
            answer = response.choices[0].message["content"].strip()
        except Exception as e:
            answer = f"AI error: {e}"
        # Increment usage
        user.ai_query_usage += 1
        await db.commit()
        await db.refresh(user)
        return ChatResponse(answer=answer, usage=user.ai_query_usage, limit=limit, plan=plan, reached_limit=False)

    @staticmethod
    async def get_usage(db, supabase_user_id: str) -> UsageResponse:
        user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
        if not user:
            return UsageResponse(usage=0, limit=STARTER_LIMIT, plan="starter", reached_limit=True)
        now = datetime.utcnow()
        if not user.ai_usage_reset or user.ai_usage_reset.month != now.month or user.ai_usage_reset.year != now.year:
            user.ai_query_usage = 0
            user.ai_usage_reset = now
            await db.commit()
            await db.refresh(user)
        plan = user.plan or "starter"
        limit = STARTER_LIMIT if plan == "starter" else 2000 if plan == "pro" else float('inf')
        reached_limit = user.ai_query_usage >= limit
        return UsageResponse(usage=user.ai_query_usage, limit=limit, plan=plan, reached_limit=reached_limit)

    @staticmethod
    async def ask_public(db, shop_name: str, question: str) -> ChatResponse:
        user = await UserRepository.get_by_shop_name(db, shop_name)
        if not user:
            return ChatResponse(answer="Shop not found.", reached_limit=True)
        now = datetime.utcnow()
        if not user.ai_usage_reset or user.ai_usage_reset.month != now.month or user.ai_usage_reset.year != now.year:
            user.ai_query_usage = 0
            user.ai_usage_reset = now
            await db.commit()
            await db.refresh(user)
        plan = user.plan or "starter"
        limit = STARTER_LIMIT if plan == "starter" else 2000 if plan == "pro" else float('inf')
        if user.ai_query_usage >= limit:
            return ChatResponse(answer="This business has reached its monthly AI query limit.", usage=user.ai_query_usage, limit=limit, plan=plan, reached_limit=True)
        openai.api_key = settings.OPENAI_API_KEY
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": f"You are answering questions for {shop_name}."}, {"role": "user", "content": question}],
                max_tokens=256,
                temperature=0.7
            )
            answer = response.choices[0].message["content"].strip()
        except Exception as e:
            answer = f"AI error: {e}"
        user.ai_query_usage += 1
        await db.commit()
        await db.refresh(user)
        return ChatResponse(answer=answer, usage=user.ai_query_usage, limit=limit, plan=plan, reached_limit=False)

    @staticmethod
    async def get_usage_public(db, shop_name: str) -> UsageResponse:
        user = await UserRepository.get_by_shop_name(db, shop_name)
        if not user:
            return UsageResponse(usage=0, limit=STARTER_LIMIT, plan="starter", reached_limit=True)
        now = datetime.utcnow()
        if not user.ai_usage_reset or user.ai_usage_reset.month != now.month or user.ai_usage_reset.year != now.year:
            user.ai_query_usage = 0
            user.ai_usage_reset = now
            await db.commit()
            await db.refresh(user)
        plan = user.plan or "starter"
        limit = STARTER_LIMIT if plan == "starter" else 2000 if plan == "pro" else float('inf')
        reached_limit = user.ai_query_usage >= limit
        return UsageResponse(usage=user.ai_query_usage, limit=limit, plan=plan, reached_limit=reached_limit)
