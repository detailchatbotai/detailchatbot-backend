from fastapi import FastAPI
from app.core.database import engine
from app.models.shop import Base as ShopBase
#from app.models.booking import Base as BookingBase
from app.api.routers.shop import router as shop_router
from app.api.routers.chat import router as chat_router

app = FastAPI(title="DetailChatBot API")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # ensure tables exist
        await conn.run_sync(ShopBase.metadata.create_all)
        #await conn.run_sync(BookingBase.metadata.create_all)

app.include_router(shop_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.get("/health")(lambda: {"status": "OK"})
