from pydantic import BaseModel, ConfigDict

class ChatRequest(BaseModel):
    shopId: str
    userMessage: str

class ChatResponse(BaseModel):
    reply: str

    model_config = ConfigDict(from_attributes=True)
