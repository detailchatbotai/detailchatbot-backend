from fastapi import FastAPI
from app.core.database import engine, Base
from app.api.routers.shop    import router as shop_router
from app.api.routers.chat    import router as chat_router
from app.api.routers.booking import router as booking_router
from app.api.routers.billing import router as billing_router

app = FastAPI(title="DetailChatBot API")

@app.on_event("startup")
async def on_startup():
    """
    Create all tables defined on Base.metadata (shops, bookings, etc.)
    in the proper order so that foreign keys resolve cleanly.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Mount all API routers under /api
app.include_router(shop_router,    prefix="/api")
app.include_router(chat_router,    prefix="/api")
app.include_router(booking_router, prefix="/api")
app.include_router(billing_router, prefix="/api")

@app.get("/health")
async def health():
    """
    Simple health check endpoint.
    """
    return {"status": "OK"}
