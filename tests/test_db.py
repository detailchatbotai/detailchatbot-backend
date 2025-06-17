import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def test_connection():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    try:
        async with engine.begin() as conn:
            # a simple round-trip query
            result = await conn.execute(text("SELECT 1"))
            print("[INFO] Database connection successful:", result.scalar())
    except Exception as e:
        print("[ERROR] Database connection failed:", e)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())