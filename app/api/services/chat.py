from app.schemas.chat import ChatResponse

async def chat_echo(user_msg: str) -> ChatResponse:
    # Temporary echo until we wire in OpenAI
    return ChatResponse(reply=f"Echo: {user_msg}")