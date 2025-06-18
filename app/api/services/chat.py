# app/api/services/chat.py
from openai import OpenAI
from app.core.config import settings
from app.schemas.chat import ChatResponse
from app.api.services.shop import get_shop
from sqlalchemy.ext.asyncio import AsyncSession

# 1. Instantiate the client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def chat_with_openai(
    user_msg: str,
    shop_id: str,
    db: AsyncSession
) -> ChatResponse:
    # 2. Fetch shop for context
    shop = await get_shop(db, shop_id)

    # 3. Build the prompt
    prompt = (
        f"You are DetailChatBot for {shop.name}.\n"
        f"Services & prices: {shop.services}\n"
        f"Customer: {user_msg}\n"
        f"Bot:"
    )

    # 4. Call the new chat endpoint
    resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=150,
    )

    # 5. Extract the reply
    text = resp.choices[0].message.content.strip()
    return ChatResponse(reply=text)
